import os
import csv
import json
import subprocess
import uuid
import fitz
from concurrent.futures import ProcessPoolExecutor, as_completed

DATASET_DIR = "dataset"
GENUINE_DIR  = os.path.join(DATASET_DIR, "genuine")
TAMPERED_DIR = os.path.join(DATASET_DIR, "tampered")
LABEL_FILE   = os.path.join(DATASET_DIR, "labels.csv")
OUTPUT_CSV   = "features.csv"

PIPELINE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_full_pipeline.py")

MAX_PAGES   = 60
NUM_WORKERS = 4

# Retry config
TIMEOUT_SECONDS = 600
MAX_RETRIES = 2


# -------------------------------
# FEATURES (Single source of truth)
# -------------------------------
FEATURE_COLUMNS = [
    "struct_score",
    "image_score",

    "ocr_similarity",
    "ocr_error_ratio",
    "font_anomaly_ratio",
    "overlap_density",
    "max_local_overlap",

    "overlap_severity",
    "ocr_layout_mismatch",
    "font_ocr_mix",
    "normalized_overlap",
    "relative_ocr_drop",

    "struct_text_conflict",
    "image_text_conflict",
    "ocr_noise_weighted",
    "extreme_overlap_flag",
    "cleanliness_score",

    "tamper_signal",
    "tamper_ratio",

    # Structural
    "num_startxref",
    "objects_with_multiple_revisions",
    "stream_length_mismatch_count",
    "metadata_mismatch",
    "time_gap_seconds",

    # Cross-modal
    "tri_modal_conflict",
]


# -------------------------------
def load_labels():
    labels = {}
    with open(LABEL_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels[row["pdf_name"]] = int(row["label"])
    return labels


# -------------------------------
def get_processed_files():
    processed = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV) as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed.add(row["pdf_name"])
    return processed


# -------------------------------
def is_large_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return len(doc) > MAX_PAGES
    except:
        return True


# -------------------------------
# CORE PIPELINE
# -------------------------------
def run_pipeline_once(pdf_path, is_large):
    job_id = uuid.uuid4().hex[:12]

    final_output_file = f"final_output_{job_id}.json"
    text_output_file  = f"text_output_{job_id}.json"
    struct_file = f"{pdf_path}.{job_id}.features.json"

    try:
        subprocess.run(
            ["python", PIPELINE_SCRIPT, pdf_path, str(is_large), job_id],
            timeout=TIMEOUT_SECONDS,
            check=False
        )

        if not os.path.exists(final_output_file) or not os.path.exists(text_output_file):
            return None

        with open(final_output_file) as f:
            final_data = json.load(f)

        with open(text_output_file) as f:
            text = json.load(f)

        # -------------------------------
        # Base features
        # -------------------------------
        struct_score = final_data.get("structural_score", 0)
        image_score  = final_data.get("image_score", 0)

        ocr_similarity     = text.get("ocr_similarity", 1.0)
        ocr_error_ratio    = text.get("ocr_error_ratio", 0)
        font_anomaly_ratio = text.get("font_anomaly_ratio", 0)
        overlap_density    = text.get("overlap_density", 0)
        max_local_overlap  = text.get("max_local_overlap", 0)

        # -------------------------------
        # Derived features
        # -------------------------------
        overlap_severity    = overlap_density * max_local_overlap
        ocr_layout_mismatch = ocr_error_ratio * overlap_density
        font_ocr_mix        = font_anomaly_ratio * ocr_error_ratio

        normalized_overlap = overlap_density / (1 + max_local_overlap)
        relative_ocr_drop  = 1 - ocr_similarity

        # -------------------------------
        # Strong features
        # -------------------------------
        struct_text_conflict = abs(struct_score - (1 - ocr_similarity))
        image_text_conflict  = abs(image_score - (1 - ocr_similarity))
        ocr_noise_weighted   = ocr_error_ratio * (1 + overlap_density)
        extreme_overlap_flag = 1 if max_local_overlap > 20 else 0
        cleanliness_score    = ocr_similarity * (1 - overlap_density)

        tri_modal_conflict = (
            abs(struct_score - image_score) +
            abs(image_score - (1 - ocr_similarity))
        )

        tamper_signal = (
            2.5 * ocr_error_ratio +
            2.0 * overlap_density +
            1.5 * (max_local_overlap / 10) +
            1.5 * font_anomaly_ratio +
            2.0 * (1 - ocr_similarity) +
            1.5 * struct_text_conflict +
            1.0 * image_text_conflict
        )

        tamper_ratio = tamper_signal / (1 + struct_score + image_score)

        # -------------------------------
        # Structural features
        # -------------------------------
        num_startxref = 0
        objects_with_multiple_revisions = 0
        stream_length_mismatch_count = 0
        metadata_mismatch = 0
        time_gap_seconds = 0

        if os.path.exists(struct_file):
            try:
                with open(struct_file) as f:
                    struct_json = json.load(f)
        
                # Direct field
                num_startxref = struct_json.get("num_startxref", 0)
        
                # Nested
                objects_with_multiple_revisions = struct_json.get(
                    "objects", {}
                ).get("objects_with_multiple_revisions", 0)
        
                stream_length_mismatch_count = struct_json.get(
                    "streams", {}
                ).get("stream_length_mismatch_count", 0)
        
                metadata_mismatch = int(
                    struct_json.get("metadata_mismatch_creator_producer", False)
                )
        
                # Handle None safely
                time_gap_seconds = struct_json.get(
                    "metadata", {}
                ).get("creation_modification_time_gap_seconds", 0)
        
                if time_gap_seconds is None:
                    time_gap_seconds = 0
        
                # -------------------------------
                # Normalization (VERY IMPORTANT)
                # -------------------------------
                time_gap_seconds = min(time_gap_seconds / 86400, 365)  # days
                num_startxref = min(num_startxref, 10)
                objects_with_multiple_revisions = min(objects_with_multiple_revisions, 20)
                stream_length_mismatch_count = min(stream_length_mismatch_count, 50)
        
            except Exception as e:
                print(f"[STRUCT ERROR] {pdf_path}: {e}")

        return {
            "struct_score": struct_score,
            "image_score": image_score,

            "ocr_similarity": ocr_similarity,
            "ocr_error_ratio": ocr_error_ratio,
            "font_anomaly_ratio": font_anomaly_ratio,
            "overlap_density": overlap_density,
            "max_local_overlap": max_local_overlap,

            "overlap_severity": overlap_severity,
            "ocr_layout_mismatch": ocr_layout_mismatch,
            "font_ocr_mix": font_ocr_mix,
            "normalized_overlap": normalized_overlap,
            "relative_ocr_drop": relative_ocr_drop,

            "struct_text_conflict": struct_text_conflict,
            "image_text_conflict": image_text_conflict,
            "ocr_noise_weighted": ocr_noise_weighted,
            "extreme_overlap_flag": extreme_overlap_flag,
            "cleanliness_score": cleanliness_score,

            "tamper_signal": tamper_signal,
            "tamper_ratio": tamper_ratio,

            "num_startxref": num_startxref,
            "objects_with_multiple_revisions": objects_with_multiple_revisions,
            "stream_length_mismatch_count": stream_length_mismatch_count,
            "metadata_mismatch": metadata_mismatch,
            "time_gap_seconds": time_gap_seconds,

            "tri_modal_conflict": tri_modal_conflict,
        }

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {pdf_path}")
        return None

    finally:
        for path in [
            final_output_file,
            text_output_file,
            struct_file,
            f"image_output_{job_id}.json",
        ]:
            try:
                os.remove(path)
            except:
                pass


# -------------------------------
def run_pipeline_with_retry(pdf_path, is_large):
    for attempt in range(MAX_RETRIES + 1):
        result = run_pipeline_once(pdf_path, is_large)

        if result is not None:
            return result

        print(f"[RETRY {attempt+1}] {pdf_path}")

    return None


# -------------------------------
def process_one(args):
    file, pdf_path, is_large = args

    print(f"[START] {file}")
    features = run_pipeline_with_retry(pdf_path, is_large)

    if features is None:
        print(f"[FAIL]  {file}")
    else:
        print(f"[DONE]  {file}")

    return file, features


# -------------------------------
def process_all():
    labels = load_labels()
    processed_files = get_processed_files()

    work_items = []

    for folder in [GENUINE_DIR, TAMPERED_DIR]:
        for file in sorted(os.listdir(folder)):
            if not file.endswith(".pdf"):
                continue

            if file in processed_files:
                continue

            pdf_path = os.path.join(folder, file)
            large = is_large_pdf(pdf_path)

            work_items.append((file, pdf_path, large))

    print(f"\n🚀 Processing {len(work_items)} PDFs\n")

    failed_files = []

    with open(OUTPUT_CSV, "a", newline="") as csv_file:
        writer = csv.writer(csv_file)

        if not os.path.exists(OUTPUT_CSV) or os.stat(OUTPUT_CSV).st_size == 0:
            writer.writerow(["pdf_name"] + FEATURE_COLUMNS + ["label"])

        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(process_one, item): item[0] for item in work_items}

            for future in as_completed(futures):
                file, features = future.result()

                if features is None:
                    failed_files.append(file)
                    continue

                row = [file] + [features.get(col, 0) for col in FEATURE_COLUMNS] + [labels.get(file, 0)]
                writer.writerow(row)
                csv_file.flush()

    print(f"\n⚠️ Failed files: {len(failed_files)}")
    print("\n✅ Feature extraction complete.")


if __name__ == "__main__":
    process_all()