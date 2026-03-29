import fitz

def highlight_suspicious(pdf_path, spans, output="highlighted.pdf"):
    doc = fitz.open(pdf_path)

    for s in spans:
        if s.get("suspicious", False):
            rect = fitz.Rect(s["bbox"])
            page = doc[s["page"]]
            page.add_rect_annot(rect)

    doc.save(output)