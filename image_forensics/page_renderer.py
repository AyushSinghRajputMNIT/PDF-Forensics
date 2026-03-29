import fitz
import os

def render_pdf_to_images(pdf_path, output_dir="rendered_pages"):
    print("\n[ALT] Rendering PDF pages as images...")

    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    image_paths = []

    total_pages = len(doc)

    for i in range(total_pages):
        print(f"   → Rendering page {i+1}/{total_pages}")

        page = doc.load_page(i)
        pix = page.get_pixmap()

        path = os.path.join(output_dir, f"page_{i}.png")
        pix.save(path)

        image_paths.append(path)

    print(f"   ✔ Rendered {len(image_paths)} pages as images\n")
    return image_paths