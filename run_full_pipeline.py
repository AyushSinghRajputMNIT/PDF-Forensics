import json
import subprocess
import os
import sys
from fusion_model import *

PDF_PATH = sys.argv[1]

# Handle optional arguments
is_large = False
if len(sys.argv) > 2:
    is_large = sys.argv[2] == "True"

# Optional job_id for parallel runs — each worker gets unique output filenames
# so workers never overwrite each other's intermediate files.
# Usage: python run_full_pipeline.py input.pdf False worker_42
job_id = sys.argv[3] if len(sys.argv) > 3 else "default"

# All intermediate + final output files are scoped to this job_id
structural_output_file = f"structural_output_{job_id}.json"
text_output_file       = f"text_output_{job_id}.json"
image_output_file      = f"image_output_{job_id}.json"
final_output_file      = f"final_output_{job_id}.json"
features_file          = PDF_PATH + f".{job_id}.features.json"

# Project directory = directory this script lives in.
# All sub-scripts are resolved relative to it, so they are always found
# regardless of where the caller's cwd is.
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def proj(script):
    """Return absolute path to a script in the project directory."""
    return os.path.join(PROJECT_DIR, script)

print("\n==============================")
print(" FULL PDF FORENSICS PIPELINE ")
print("==============================")

# -------------------------------
# STEP 1: STRUCTURAL ANALYSIS
# -------------------------------
print("\n[STEP 1] Structural Analysis")

subprocess.run([
    "python", proj("extract_structural_features.py"),
    PDF_PATH,
    "-o", features_file,
])

subprocess.run([
    "python", proj("analyze_structural_features.py"),
    features_file,
    "-o", structural_output_file,
    "--pretty",
])

with open(structural_output_file) as f:
    struct_data = json.load(f)

struct_score = struct_data["analysis"]["structural_suspicion_score"] / 100

# -------------------------------
# STEP 2: TEXTUAL ANALYSIS
# -------------------------------
print("\n[STEP 2] Textual Analysis")

subprocess.run([
    "python", proj("run_textual_analysis.py"),
    PDF_PATH,
    str(is_large),
    text_output_file,   # pass output path so the script writes here
])

with open(text_output_file) as f:
    text_data = json.load(f)

text_score = compute_textual_score(text_data)

# -------------------------------
# STEP 3: IMAGE ANALYSIS
# -------------------------------
print("\n[STEP 3] Image Analysis")

subprocess.run([
    "python", proj("run_image_analysis.py"),
    PDF_PATH,
    image_output_file,  # pass output path so the script writes here
])

with open(image_output_file) as f:
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
category    = classify(final_score)

print("\n===== FINAL RESULT =====")
print(f"Forgery Probability: {final_score:.2f}")
print(f"Category: {category}")

final_output = {
    "structural_score": struct_score,
    "textual_score":    text_score,
    "image_score":      image_score,
    "final_score":      final_score,
    "category":         category,
}

with open(final_output_file, "w") as f:
    json.dump(final_output, f, indent=2)

print(f"✔ Saved final result → {final_output_file}")