import json
import subprocess
import os
import sys
from fusion_model import *

PDF_PATH = sys.argv[1]

# Handle optional argument
is_large = False
if len(sys.argv) > 2:
    is_large = sys.argv[2] == "True"

print("\n==============================")
print(" FULL PDF FORENSICS PIPELINE ")
print("==============================")

# -------------------------------
# STEP 1: STRUCTURAL ANALYSIS
# -------------------------------
print("\n[STEP 1] Structural Analysis")

# Extract features
subprocess.run([
    "python", "extract_structural_features.py", PDF_PATH
])

features_file = PDF_PATH + ".features.json"

# Analyze
subprocess.run([
    "python", "analyze_structural_features.py",
    features_file,
    "-o", "structural_output.json",
    "--pretty"
])

# Load structural result
with open("structural_output.json") as f:
    struct_data = json.load(f)

struct_score = struct_data["analysis"]["structural_suspicion_score"] / 100

# -------------------------------
# STEP 2: TEXTUAL ANALYSIS
# -------------------------------
print("\n[STEP 2] Textual Analysis")

subprocess.run([
    "python", "run_textual_analysis.py", PDF_PATH, str(is_large)
])

with open("text_output.json") as f:
    text_data = json.load(f)

text_score = compute_textual_score(text_data)

# -------------------------------
# STEP 3: IMAGE ANALYSIS
# -------------------------------
print("\n[STEP 3] Image Analysis")

subprocess.run([
    "python", "run_image_analysis.py", PDF_PATH
])

with open("image_output.json") as f:
    image_data = json.load(f)

image_score = compute_image_score(image_data)

# -------------------------------
# STEP 4: FUSION
# -------------------------------
print("\n[STEP 4] Fusion Model")

print(f"Structural Score: {struct_score:.2f}")
print(f"Textual Score:   {text_score:.2f}")
print(f"Image Score:     {image_score:.2f}")

final_score = fuse_scores(struct_score, text_score, image_score)
category = classify(final_score)

print("\n===== FINAL RESULT =====")
print(f"Forgery Probability: {final_score:.2f}")
print(f"Category: {category}")

# Save final output
final_output = {
    "structural_score": struct_score,
    "textual_score": text_score,
    "image_score": image_score,
    "final_score": final_score,
    "category": category
}

with open("final_output.json", "w") as f:
    json.dump(final_output, f, indent=2)

print("✔ Saved final result → final_output.json")