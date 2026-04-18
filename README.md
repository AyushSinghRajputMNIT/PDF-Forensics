# 🕵️ PDF Forgery Detection using Multi-Modal Forensics + ML

### B.Tech CSE Major Project

This project implements a **production-grade PDF forensics system** that detects document tampering using **multi-modal analysis + machine learning + explainability**.

It analyzes PDFs across multiple layers:

- 📄 Structural (low-level PDF internals)
- 📝 Textual (OCR, fonts, layout consistency)
- 🖼️ Image (visual artifacts & compression)
- 🤖 ML Model (learned patterns from engineered features)
- 🧠 Explainability (SHAP + domain insights)

---

## 🔍 Problem Statement

PDF forgery detection is difficult because manipulation can occur across different layers:

- Structural edits (xref tables, object revisions, streams)
- Textual inconsistencies (font changes, layout mismatch)
- Image tampering (signatures, stamps, scanned edits)

This project builds a **multi-modal forensic pipeline + ML classifier** to automatically detect such anomalies and produce:

- ✔ Forgery probability
- ✔ Risk level
- ✔ Human-readable explanation

---

## 🎯 Objectives

- Analyze low-level PDF structure
- Detect OCR and layout inconsistencies
- Identify image-level tampering artifacts
- Engineer strong forensic features
- Train ML models (RF + XGBoost + Ensemble)
- Apply threshold tuning for optimal decisions
- Provide **industry-level explainability (SHAP + domain logic)**

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
           FEATURE BUILDER (core logic)
                     │
            ML MODEL (Ensemble)
                     │
      PROBABILITY + THRESHOLD DECISION
                     │
     SHAP + DOMAIN EXPLANATION ENGINE
                     │
               FINAL OUTPUT
```

---

## 🧩 Modules

### 🔹 Structural Analysis

Extracts deep PDF internals:

- XRef tables
- Object revisions
- Stream consistency
- Metadata consistency

Detects:

- Multiple `startxref`
- Object version conflicts
- Stream length mismatches
- Metadata inconsistencies

📌 **Key Insight:** Structural tampering is the **strongest signal**.

---

### 🔹 Textual Analysis

- Extracts text + font metadata
- Performs OCR using Tesseract
- Compares OCR vs embedded text

Detects:

- OCR mismatch
- Font anomalies
- Layout inconsistencies
- Overlapping text regions

📌 OCR is skipped for large PDFs for performance.

---

### 🔹 Image Analysis

- Extracts images OR renders pages
- Uses:
  - Error Level Analysis (ELA)
  - CNN-based scoring

Detects:

- Compression inconsistencies
- Visual tampering

---

### 🔹 Feature Builder (🔥 CORE)

File: `feature_builder.py`

Single source of truth for features used in training + inference.

#### Feature Categories

**Base Features**

- struct_score, image_score
- ocr_similarity, ocr_error_ratio

**Derived Features**

- overlap_severity
- normalized_overlap
- relative_ocr_drop

**Strong Features**

- struct_text_conflict
- image_text_conflict
- ocr_noise_weighted
- cleanliness_score

**Structural Features (Most Important)**

- num_startxref
- stream_length_mismatch_count
- metadata_mismatch
- time_gap_seconds

**Fusion Features**

- tamper_signal
- tamper_ratio

---

### 🔹 Machine Learning Model

Models used:

- Random Forest
- XGBoost
- Ensemble

Enhancements:

- GroupKFold (no leakage)
- Balanced dataset
- Feature engineering
- Threshold tuning

---

### 🔥 Threshold Tuning (Critical)

Instead of fixed 0.5:

Best threshold ≈ **0.54**

Improves:

- Accuracy
- Precision/Recall balance
- Real-world reliability

---

### 🔹 Explainability Engine

File: `predict.py`

#### 1. SHAP (Model-based)

- Feature contribution scores
- Why model predicted tampered

#### 2. Domain Logic

- Human-readable forensic reasoning

#### 3. Hybrid Output

- Combines both

Example:

- HIGH: Multiple xref sections detected
- HIGH: Stream mismatch detected
- MEDIUM: OCR inconsistency

---

## 📊 Dataset

```
dataset/
├── genuine/
├── tampered/
├── labels.csv
```

Tampering includes:

- Structural edits
- Metadata changes
- Re-saved PDFs

---

## ⚡ Feature Extraction Pipeline

File: `generate_features.py`

- Runs full pipeline
- Uses `feature_builder.py`
- Saves to `features.csv`

Features:

- Resume support
- Parallel processing
- Retry mechanism

---

## 🤖 Model Performance

| Model         | Accuracy   |
| ------------- | ---------- |
| Random Forest | **88.33%** |
| XGBoost       | 85.00%     |
| Ensemble      | **88.33%** |

📌 RF dominates → ensemble weight = 0.0

---

## 🧠 Feature Importance

Top signals:

- num_startxref ⭐⭐⭐⭐⭐
- time_gap_seconds ⭐⭐⭐⭐
- stream_length_mismatch_count ⭐⭐⭐⭐
- ocr_noise_weighted ⭐⭐⭐
- ocr_layout_mismatch ⭐⭐⭐

---

## ▶️ How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run pipeline

```bash
python run_full_pipeline.py sample.pdf
```

### Generate dataset

```bash
python generate_features.py
```

### Train model

```bash
python train_model_ensemble.py
```

### Predict (FINAL)

```bash
python predict.py sample.pdf
```

---

## 📊 Final Output

```json
{
  "probability": 0.91,
  "threshold": 0.54,
  "prediction": "TAMPERED",
  "risk_level": "HIGH",
  "top_features": [
    "num_startxref",
    "time_gap_seconds",
    "stream_length_mismatch_count"
  ],
  "explanation": [
    "Multiple xref sections detected",
    "Metadata time gap indicates modification",
    "Stream inconsistencies found"
  ]
}
```

---

## ⚠️ Limitations

- OCR noise possible
- Moderate dataset size
- CNN not domain-trained
- Some false positives

---

## 🚀 Future Work

- Train forensic CNN
- Layout-aware models (LayoutLM)
- Visual tamper heatmaps
- Web UI
- API deployment

---

## 📌 Project Status

| Component           | Status |
| ------------------- | ------ |
| Structural Analysis | ✅     |
| Textual Analysis    | ✅     |
| Image Analysis      | ✅     |
| Feature Engineering | ✅     |
| ML Training         | ✅     |
| Threshold Tuning    | ✅     |
| Explainability      | ✅     |
| Production System   | ✅     |

---

## 👨‍💻 Author

**Ayush Singh Rajput**
B.Tech CSE (2026), MNIT Jaipur

---

## 🧠 Key Achievement

Evolution:

Rule-based → Multi-modal → ML → Threshold tuning → Explainable AI

👉 Result: **Production-ready PDF forgery detection system**
