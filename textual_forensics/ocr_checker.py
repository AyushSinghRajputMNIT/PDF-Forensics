import pytesseract
from PIL import Image
import fitz
from difflib import SequenceMatcher
import numpy as np

import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def compute_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def run_ocr_analysis(pdf_path, spans):
    print("\n[3/4] Running OCR consistency analysis...")

    doc = fitz.open(pdf_path)

    similarities = []
    mismatch_count = 0

    total = len(spans)

    for i, span in enumerate(spans):
        if i % max(1, total // 10) == 0:
            print(f"   → OCR Progress: {(i/total)*100:.1f}%")

        text = span["text"].strip()
        if not text:
            continue

        page = doc.load_page(span["page"])
        rect = fitz.Rect(span["bbox"])

        try:
            pix = page.get_pixmap(clip=rect)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            ocr_text = pytesseract.image_to_string(img).strip()

            sim = compute_similarity(text, ocr_text)
            similarities.append(sim)

            if sim < 0.7:
                mismatch_count += 1

        except:
            continue

    avg_similarity = np.mean(similarities) if similarities else 1.0

    print(f"   ✔ OCR similarity: {avg_similarity:.3f}")
    print(f"   ✔ OCR mismatches: {mismatch_count}\n")

    return {
        "ocr_similarity": float(avg_similarity),
        "ocr_mismatch_count": mismatch_count
    }