from textual_forensics.text_and_font_extractor import extract_text_and_fonts
from textual_forensics.layout_analyzer import analyze_layout
from textual_forensics.ocr_checker import run_ocr_analysis
from textual_forensics.anomaly_detector import sliding_window_entropy
from textual_forensics.highlight_pdf import highlight_suspicious

import sys
import json
import time

pdf_path = sys.argv[1]

print("\n==============================")
print(" PDF TEXTUAL FORENSICS MODULE ")
print("==============================")

start_time = time.time()

# Step 1
spans = extract_text_and_fonts(pdf_path)

# Step 2
layout_features = analyze_layout(spans)

# Step 3
ocr_features = run_ocr_analysis(pdf_path, spans)

# Step 4
font_features = sliding_window_entropy(spans)

# Merge all features
final_features = {
    **layout_features,
    **ocr_features,
    **font_features
}

highlight_suspicious(pdf_path, spans, output="highlighted.pdf")

end_time = time.time()

print("\n✔ Textual Analysis Complete!")
print(f"⏱ Total Time: {end_time - start_time:.2f} seconds")

print("\n===== FINAL OUTPUT =====")
print(json.dumps(final_features, indent=2))

# SAVE OUTPUT
with open("text_output.json", "w") as f:
    json.dump(final_features, f, indent=2)

print("✔ Saved textual output → text_output.json")
