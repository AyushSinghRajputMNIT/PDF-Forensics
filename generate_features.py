import os
import csv
import json
import subprocess
import fitz  # PyMuPDF

DATASET_DIR = "dataset"
GENUINE_DIR = os.path.join(DATASET_DIR, "genuine")
TAMPERED_DIR = os.path.join(DATASET_DIR, "tampered")
LABEL_FILE = os.path.join(DATASET_DIR, "labels.csv")
OUTPUT_CSV = "features.csv"

PIPELINE_SCRIPT = "run_full_pipeline.py"

MAX_PAGES = 20  # threshold for OCR skipping


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
# Already processed files
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
# Check if large PDF
# -------------------------------
def is_large_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        return len(doc) > MAX_PAGES
    except:
        return True


# -------------------------------
# Run pipeline
# -------------------------------
def run_pipeline(pdf_path, is_large):
    try:
        subprocess.run([
            "python", PIPELINE_SCRIPT,
            pdf_path,
            str(is_large)
        ])

        if not os.path.exists("final_output.json"):
            print(f"[ERROR] Missing final_output.json for {pdf_path}")
            return None

        with open("final_output.json") as f:
            data = json.load(f)

        return {
            "struct_score": data.get("structural_score", 0),
            "text_score": data.get("textual_score", 0),
            "image_score": data.get("image_score", 0),
            "final_score": data.get("final_score", 0)
        }

    except Exception as e:
        print(f"[ERROR] {pdf_path}: {e}")
        return None


# -------------------------------
# Main
# -------------------------------
def process_all():
    labels = load_labels()
    processed_files = get_processed_files()

    file_exists = os.path.isfile(OUTPUT_CSV)

    with open(OUTPUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)

        # Header once
        if not file_exists:
            writer.writerow([
                "pdf_name",
                "struct_score",
                "text_score",
                "image_score",
                "final_score",
                "label"
            ])

        for folder in [GENUINE_DIR, TAMPERED_DIR]:
            for file in os.listdir(folder):

                if not file.endswith(".pdf"):
                    continue

                if file in processed_files:
                    print(f"[SKIP] Already processed: {file}")
                    continue

                pdf_path = os.path.join(folder, file)

                print(f"\n[INFO] Processing: {file}")

                # Check size
                large = is_large_pdf(pdf_path)
                if large:
                    print(f"[INFO] Large PDF → OCR will be skipped")

                features = run_pipeline(pdf_path, large)

                if features is None:
                    print(f"[SKIP] Failed: {file}")
                    continue

                row = [
                    file,
                    features["struct_score"],
                    features["text_score"],
                    features["image_score"],
                    features["final_score"],
                    labels.get(file, 0)
                ]

                writer.writerow(row)
                f.flush()  # 🔥 immediate save

                print(f"[DONE] {file}")

    print("\n✅ Feature extraction complete.")


if __name__ == "__main__":
    process_all()