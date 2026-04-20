import sys
import json
import time
import os

from image_forensics.image_extractor import extract_images_with_meta
from image_forensics.image_features import extract_image_features
from image_forensics.page_renderer import render_pdf_to_images

pdf_path = sys.argv[1]
output_path = sys.argv[2] if len(sys.argv) > 2 else "image_output.json"

print("\n==============================")
print(" PDF IMAGE FORENSICS MODULE ")
print("==============================")

start_time = time.time()

# STEP 1: Extract embedded images WITH metadata
print("\n[STEP 1/3] Extracting embedded images")
images_meta = extract_images_with_meta(pdf_path)

image_paths = [img["path"] for img in images_meta]

# fallback
if len(image_paths) == 0:
    print("⚠ No embedded images → switching to page rendering")
    image_paths = render_pdf_to_images(pdf_path)
    images_meta = [{"path": p, "type": "page"} for p in image_paths]

# STEP 2
print("\n[STEP 2/3] Feature extraction")
features = extract_image_features(images_meta)

# STEP 3
print("\n[STEP 3/3] Finalizing")

end_time = time.time()

print("\n✔ Done")
print(f"⏱ Time: {end_time - start_time:.2f}s")

with open(output_path, "w") as f:
    json.dump(features, f, indent=2)

print(f"✔ Saved → {output_path}")

# cleanup tmp images
for img in images_meta:
    path = img.get("path")
    if path and path.startswith("tmp_img_"):
        try:
            os.remove(path)
        except:
            pass