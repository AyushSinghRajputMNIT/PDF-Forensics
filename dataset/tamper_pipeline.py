import os
import shutil
import random
import csv
import pikepdf
import fitz  # PyMuPDF

GENUINE_DIR = "dataset/genuine"
TAMPERED_DIR = "dataset/tampered"
LABEL_FILE = "dataset/labels.csv"

os.makedirs(TAMPERED_DIR, exist_ok=True)

labels = []

def tamper_metadata(input_path, output_path):
    try:
        pdf = pikepdf.open(input_path)
        pdf.docinfo["/Author"] = "Hacker_" + str(random.randint(100,999))
        pdf.save(output_path)
        return True
    except:
        return False

def tamper_resave(input_path, output_path):
    try:
        doc = fitz.open(input_path)
        doc.save(output_path)
        return True
    except:
        return False

def process():
    files = [f for f in os.listdir(GENUINE_DIR) if f.endswith(".pdf")]

    for file in files:
        input_path = os.path.join(GENUINE_DIR, file)

        # ---- Add Genuine Entry ----
        labels.append([file, 0, "none"])

        # ---- Metadata Tamper ----
        out_meta = file.replace(".pdf", "_meta.pdf")
        meta_path = os.path.join(TAMPERED_DIR, out_meta)

        if tamper_metadata(input_path, meta_path):
            labels.append([out_meta, 1, "metadata"])

        # ---- Re-save Tamper ----
        out_resave = file.replace(".pdf", "_resave.pdf")
        resave_path = os.path.join(TAMPERED_DIR, out_resave)

        if tamper_resave(input_path, resave_path):
            labels.append([out_resave, 1, "resave"])

    # ---- Save Labels ----
    with open(LABEL_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pdf_name", "label", "tamper_type"])
        writer.writerows(labels)

    print("✅ Tampering complete. Labels generated.")

if __name__ == "__main__":
    process()