import os
import csv
import json
import subprocess
import uuid
import fitz
from concurrent.futures import ProcessPoolExecutor, as_completed

from feature_builder import build_features, FEATURE_COLUMNS


DATASET_DIR = "dataset"
GENUINE_DIR  = os.path.join(DATASET_DIR, "genuine")
TAMPERED_DIR = os.path.join(DATASET_DIR, "tampered")
LABEL_FILE   = os.path.join(DATASET_DIR, "labels.csv")
OUTPUT_CSV   = "features.csv"

PIPELINE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_full_pipeline.py")

MAX_PAGES   = 60
NUM_WORKERS = 1

TIMEOUT_SECONDS = 600
MAX_RETRIES = 2


# -------------------------------
# Load labels
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
    image_output_file = f"image_output_{job_id}.json"

    # 🔥 IMPORTANT: structural file lives alongside PDF
    struct_file = f"{pdf_path}.{job_id}.features.json"

    try:
        subprocess.run(
            ["python", PIPELINE_SCRIPT, pdf_path, str(is_large), job_id],
            timeout=TIMEOUT_SECONDS,
            check=False
        )

        if (not os.path.exists(final_output_file) or not os.path.exists(text_output_file) or not os.path.exists(image_output_file)) :
            return None

        with open(final_output_file) as f:
            final_data = json.load(f)

        with open(text_output_file) as f:
            text_data = json.load(f)

        with open(image_output_file) as f:
            image_data = json.load(f)

        # 🔥 ALL FEATURE LOGIC MOVED HERE
        features = build_features(
            final_data=final_data,
            text_data=text_data,
            image_data=image_data,
            struct_json_path=struct_file
        )

        return features

    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {pdf_path}")
        return None

    finally:
        for path in [
            final_output_file,
            text_output_file,
            image_output_file,
            struct_file,
        ]:
            try:
                os.remove(path)
            except:
                pass
        # delete structural_output files
        for file in os.listdir("."):
            if file.startswith(f"structural_output_{job_id}"):
                try:
                    os.remove(file)
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

    write_header = not os.path.exists(OUTPUT_CSV) or os.stat(OUTPUT_CSV).st_size == 0

    with open(OUTPUT_CSV, "a", newline="") as csv_file:
        writer = csv.writer(csv_file)

        if write_header:
            writer.writerow(["pdf_name"] + FEATURE_COLUMNS + ["label"])
        if NUM_WORKERS == 1:
            for item in work_items:
                file, features = process_one(item)

                if features is None:
                    failed_files.append(file)
                    continue

                row = [file] + [features.get(col, 0) for col in FEATURE_COLUMNS] + [labels.get(file, 0)]
                writer.writerow(row)
                csv_file.flush()
        else:

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