import fitz
import os
import io
from PIL import Image

def extract_images_with_meta(pdf_path):
    doc = fitz.open(pdf_path)

    results = []

    for page_index, page in enumerate(doc):
        images = page.get_images(full=True)

        for img in images:
            xref = img[0]

            base = doc.extract_image(xref)
            img_bytes = base["image"]

            ext = base.get("ext", "png")

            path = f"tmp_img_{page_index}_{xref}.{ext}"

            with open(path, "wb") as f:
                f.write(img_bytes)

            rects = page.get_image_rects(xref)
            img_type = "unknown"

            if rects:
                w, h = rects[0].width, rects[0].height

                if w > 200 and h > 80:
                    img_type = "logo"
                elif w > h * 2:
                    img_type = "signature"
                else:
                    img_type = "stamp"

            results.append({
                "path": path,
                "type": img_type,
                "source": "embedded"
            })

    return results