import fitz

def extract_text_and_fonts(pdf_path):
    print("\n[1/4] Extracting text + font information...")

    doc = fitz.open(pdf_path)
    spans = []

    total_pages = len(doc)

    for page_index in range(total_pages):
        page = doc.load_page(page_index)

        print(f"   → Page {page_index+1}/{total_pages} ({(page_index+1)/total_pages*100:.1f}%)")

        blocks = page.get_text("dict")["blocks"]

        for b in blocks:
            if b["type"] == 0:
                for line in b["lines"]:
                    for span in line["spans"]:
                        spans.append({
                            "text": span["text"],
                            "font": span["font"],
                            "size": span["size"],
                            "bbox": span["bbox"],
                            "page": page_index
                        })

    print(f"   ✔ Extracted {len(spans)} text spans\n")
    return spans