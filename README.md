# 🕵️ PDF Forgery Detection using Multi-Modal Forensics

### B.Tech CSE Major Project

This project implements an automated **PDF forensics system** that detects document tampering by analyzing multiple layers of a PDF:

- 📄 Structural (low-level PDF objects)
- 📝 Textual (fonts, layout, OCR consistency)
- 🖼️ Image (visual and compression artifacts)

The system combines these signals using a **fusion model** to produce a **forgery probability score** and classification.

---

## 🔍 Problem Statement

Detecting forged or tampered PDFs is challenging because manipulation can occur at multiple levels:

- Structural edits (xref tables, objects, streams)
- Textual modifications (font changes, alignment issues)
- Image alterations (signatures, stamps, scanned regions)

This project builds an automated **multi-modal forensic framework** to identify such inconsistencies.

---

## 🎯 Objectives

- Analyze low-level PDF structure
- Detect textual anomalies and inconsistencies
- Identify image-level tampering artifacts
- Combine signals into a final forgery probability
- Build a dataset and ML model for classification
- Provide interpretable outputs for analysis

---

## ⚙️ System Architecture

```
                INPUT PDF
                     │
     ┌───────────────┼────────────────┐
     │               │                │
STRUCTURAL      TEXTUAL          IMAGE
 ANALYSIS        ANALYSIS         ANALYSIS
     │               │                │
     └───────────────┼────────────────┘
                     │
              FUSION MODEL
                     │
           FINAL FORGERY SCORE
```

---

## 🧩 Modules

### 🔹 Structural Analysis

- Extracts:
  - XRef tables
  - Object revisions
  - Streams
  - Metadata

- Detects:
  - Multiple startxref entries
  - Object inconsistencies
  - Metadata anomalies

---

### 🔹 Textual Analysis

- Extracts text + font info
- Performs:
  - Layout analysis
  - Font entropy detection
  - OCR comparison (Tesseract)

- Detects:
  - Font mismatches
  - Alignment issues
  - OCR inconsistencies

**Optimization:** OCR is automatically skipped for large PDFs for performance.

---

### 🔹 Image Analysis

- Embedded image extraction OR page rendering fallback
- Techniques:
  - Error Level Analysis (ELA)
  - CNN-based scoring

- Detects:
  - Compression artifacts
  - Visual tampering

---

### 🔹 Fusion Model

Combines multi-modal scores:

```
Final Score =
  0.4 * Structural +
  0.35 * Textual +
  0.25 * Image
```

Outputs:

- Forgery probability
- Risk category

---

### 🔹 Full Pipeline

File: `run_full_pipeline.py`

```
PDF → Structural → Textual → Image → Fusion → Output
```

---

## 📊 Dataset

A custom dataset was created using:

- Genuine PDFs (real-world documents)
- Tampered PDFs generated via:
  - Metadata manipulation
  - Structural re-saving

### Structure

```
dataset/
├── genuine/
├── tampered/
├── labels.csv
```

---

## ⚡ Feature Extraction Pipeline

File: `generate_features.py`

- Runs full pipeline on all PDFs
- Extracts:
  - structural_score
  - text_score
  - image_score
  - final_score
- Saves results incrementally → `features.csv`

### Features

- Resume capability
- Fault-tolerant execution
- Large PDF handling (OCR skipped selectively)

---

## 🤖 Machine Learning (Planned / In Progress)

- Models:
  - Random Forest
  - XGBoost (optional)

- Goals:
  - Compare rule-based vs ML performance
  - Improve accuracy
  - Reduce false positives

---

## ▶️ How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Run full pipeline

```bash
python run_full_pipeline.py sample.pdf
```

---

### 3. Generate feature dataset

```bash
python generate_features.py
```

---

### 4. Train ML model (optional)

```bash
python train_model.py
```

---

## 📊 Sample Output

```json
{
  "structural_score": 0.12,
  "textual_score": 0.3,
  "image_score": 0.05,
  "final_score": 0.24,
  "category": "MINOR_ANOMALY"
}
```

---

## ⚠️ Limitations

- CNN not trained specifically for document forensics
- OCR may introduce noise
- Some genuine PDFs may appear suspicious (false positives)
- Limited tampering types (expandable)

---

## 🚀 Future Work

- Add text tampering
- Add image tampering
- Train domain-specific CNN
- Improve OCR robustness
- Add visualization (heatmaps / highlights)
- Build UI (web/desktop)
- Explore advanced models (LayoutLM, DocFormer)

---

## 📌 Project Status

| Component           | Status      |
| ------------------- | ----------- |
| Structural Analysis | Complete    |
| Textual Analysis    | Complete    |
| Image Analysis      | Complete    |
| Fusion Model        | Complete    |
| Dataset Creation    | Complete    |
| Feature Pipeline    | Complete    |
| ML Training         | In Progress |

---

## 👨‍💻 Author

Ayush Singh Rajput  
B.Tech CSE Major Project
