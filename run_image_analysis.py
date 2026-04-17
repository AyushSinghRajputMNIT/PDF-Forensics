from image_forensics.image_extractor import extract_images
from image_forensics.image_features import extract_image_features
from image_forensics.page_renderer import render_pdf_to_images

import sys
import json
import time

pdf_path = sys.argv[1]

# Optional: caller can specify where to write output (for parallel workers).
# Falls back to the original hardcoded name so existing single-run usage is unchanged.
output_path = sys.argv[2] if len(sys.argv) > 2 else "image_output.json"

print("\n==============================")
print(" PDF IMAGE FORENSICS MODULE ")
print("==============================")

start_time = time.time()

# Step 1
print("\n[STEP 1/3] Image Extraction")
image_paths = extract_images(pdf_path)

# Fallback if no embedded images
if len(image_paths) == 0:
    print("⚠ No embedded images found → Switching to page-level analysis")
    image_paths = render_pdf_to_images(pdf_path)

# Step 2
print("\n[STEP 2/3] Image Analysis")
features = extract_image_features(image_paths)

# Step 3
print("\n[STEP 3/3] Finalizing Results")

end_time = time.time()

print("\n✔ Processing Complete!")
print(f"⏱ Total Time: {end_time - start_time:.2f} seconds")

print("\n===== FINAL OUTPUT =====")
print(json.dumps(features, indent=2))

# SAVE OUTPUT to the path specified by the caller
with open(output_path, "w") as f:
    json.dump(features, f, indent=2)

print(f"✔ Saved image output → {output_path}")