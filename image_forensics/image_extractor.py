import fitz
import os

def extract_images(pdf_path, output_dir="extracted_images"):
    print("\n[1/3] Extracting images from PDF...")
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    total_pages = len(doc)

    for page_index in range(total_pages):
        page = doc.load_page(page_index)
        images = page.get_images(full=True)

        print(f"   → Processing page {page_index+1}/{total_pages} ({(page_index+1)/total_pages*100:.1f}%)")

        for img_index, img in enumerate(images):
            xref = img[0]
            base = doc.extract_image(xref)

            image_bytes = base["image"]
            ext = base["ext"]

            filename = f"page{page_index}_img{img_index}.{ext}"
            path = os.path.join(output_dir, filename)

            with open(path, "wb") as f:
                f.write(image_bytes)

            image_paths.append(path)

    print(f"   ✔ Extracted {len(image_paths)} images\n")
    return image_paths