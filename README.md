# 🕵️ PDF Forgery Detection using Multi-Modal Forensics

### B.Tech Major Project

This project implements an automated **PDF forensics system** that analyzes documents across multiple layers—**structure, text, and images**—to detect potential tampering or forgery.

The system is currently implemented as a **research prototype pipeline**, capable of generating a **forgery probability score** along with intermediate forensic insights.

---

## 🔍 Problem Statement

Design and implement a system that analyzes a given PDF document and determines whether it has been tampered with or forged.

PDF manipulation can occur at multiple levels:

- Structural edits (xref tables, objects, streams)
- Textual modifications (font changes, alignment issues)
- Image alterations (edited signatures, stamps, scanned regions)

Manual detection is difficult and requires expertise.
This system automates the process using **multi-modal forensic analysis**.

---

## 🎯 Objectives

1. Extract and analyze **low-level PDF structural features**
2. Detect **structural inconsistencies**
3. Analyze **textual content anomalies**
4. Analyze **images / page-level renderings**
5. Combine all signals into a **final forgery probability**
6. Provide interpretable outputs and intermediate diagnostics

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

## 🧩 Modules Implemented

### 1. Structural Analysis

📄 Files:

- `extract_structural_features.py`
- `analyze_structural_features.py`

#### What it does:

- Parses raw PDF bytes
- Extracts:
  - XRef tables
  - Object revisions
  - Streams
  - Metadata
  - Image statistics

#### Detects:

- Multiple `startxref` entries
- Object revision anomalies
- Stream length mismatches
- Metadata inconsistencies

#### Output:

- `sample.pdf.features.json`
- `structural_output.json`

---

### 2. Textual Analysis

📄 Folder:

- `textual_forensics/`

#### Pipeline:

1. Extract text + font data (PyMuPDF)
2. Layout analysis (baseline + spacing)
3. OCR comparison (Tesseract)
4. Font anomaly detection (sliding window entropy)

#### Detects:

- Font mismatches
- Alignment anomalies
- OCR inconsistencies
- Suspicious font transitions

#### Output:

- Console logs with progress
- `text_output.json`
- `highlighted.pdf` (visual annotations)

---

### 3. Image Analysis

📄 Folder:

- `image_forensics/`

#### Two Modes:

**A. Embedded Image Analysis**

- Extract images from PDF
- Apply:
  - ELA (Error Level Analysis)
  - CNN-based feature extraction

**B. Page-Level Analysis (Fallback)**

- If no images found:
  - Render PDF pages as images
  - Apply same analysis

#### Detects:

- Compression inconsistencies
- Pixel-level anomalies
- Visual tampering signals

#### Output:

- `image_output.json`

---

### 4. Fusion Model

📄 File:

- `fusion_model.py`

#### Combines:

- Structural score
- Textual score
- Image score

#### Weighted scoring:

```
Final Score =
  w1 * Structural +
  w2 * Textual +
  w3 * Image
```

#### Output:

- Final forgery probability
- Risk category

---

### 5. Full Pipeline

📄 File:

- `run_full_pipeline.py`

#### Runs complete system:

```
PDF → Structural → Textual → Image → Fusion → Final Output
```

#### Output:

- `structural_output.json`
- `text_output.json`
- `image_output.json`
- `final_output.json`

---

## ▶️ How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Run Full Pipeline

```bash
python run_full_pipeline.py sample.pdf
```

---

### 3. Output Example

```
===== FINAL RESULT =====
Forgery Probability: 0.24
Category: MINOR_ANOMALY
```

---

## 📊 Sample Outputs

### Structural

- Suspicion Score: 11.2%
- Category: CLEAN/LOW_RISK

### Textual

```json
{
  "baseline_std": 208.73,
  "ocr_similarity": 0.75,
  "font_entropy": 0.86
}
```

### Image

```json
{
  "avg_ela_variance": 3.03,
  "avg_cnn_tamper_prob": 0.16
}
```

### Final

```json
{
  "forgery_score": 0.24,
  "category": "MINOR_ANOMALY"
}
```

---

## ⚠️ Current Limitations

- CNN model not trained specifically for PDF tampering
- No dataset-based learning yet (rule-based + pretrained models)
- OCR accuracy may affect results
- Some anomalies may produce false positives
- Structural parsing relies partly on regex (not fully robust)

---

## 🚀 Future Work (Next Phase)

- Dataset creation (genuine vs tampered PDFs)
- Train ML/DL models for:
  - Structural features
  - Text anomalies
  - Image tampering

- Advanced fusion (XGBoost / Neural Networks)
- Region-level heatmaps
- Full UI / application

---

## 👨‍💻 Author

**Ayush Singh Rajput**
B.Tech CSE Major Project

---

## 📌 Status

✅ Structural Analysis — Complete
✅ Textual Analysis — Complete
✅ Image Analysis — Complete (with fallback)
✅ Fusion Model — Complete
✅ Full Pipeline — Working

🟡 Dataset + ML Training — Pending
