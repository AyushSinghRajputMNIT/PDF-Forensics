# 🕵️ PDF Forgery Detection using Multi-Modal Forensics + ML

### B.Tech CSE Major Project

This project implements a production-grade PDF forensic analysis system that detects document tampering using:

- Multi-modal forensic analysis
- Machine Learning (Random Forest + XGBoost Ensemble)
- Domain-based explainability (NO SHAP)
- Backend PDF report generation

---

## 🔍 Problem Statement

PDF tampering can occur across multiple layers:

- Structural (PDF internals)
- Textual (OCR, fonts, layout)
- Image (compression artifacts, edits)
- Metadata (timestamps, inconsistencies)

Traditional tools fail to detect cross-layer inconsistencies.

This project builds a multi-modal forensic pipeline + ML system to detect such tampering and generate interpretable reports.

---

## 🎯 Objectives

- Detect structural anomalies in PDFs
- Identify textual inconsistencies using OCR
- Detect image tampering using forensic signals (no CNN)
- Build strong engineered features
- Train ML models (Random Forest + XGBoost)
- Use ensemble with threshold tuning
- Provide clear forensic explanations (domain-based)
- Generate professional PDF reports

---

## ⚙️ System Architecture

```
INPUT PDF
   │
   ├── Structural Analysis
   ├── Textual Analysis (OCR + Fonts)
   ├── Image Analysis (Signal-based: Noise + JPEG + Edge)
   │
   └── Feature Builder
            │
    ML Models (RF + XGoost)
            │
     Ensemble Decision
            │
Explainability Engine (SHAP + Rules)
            │
   API + UI + PDF Report
```

---

## 🧩 Modules

### 🔹 Structural Analysis

Detects:

- Multiple startxref
- Stream length mismatches
- Metadata inconsistencies
- Time gap anomalies

Strongest tampering signal.

---

### 🔹 Textual Analysis

- OCR using Tesseract
- Font and layout extraction

Detects:

- OCR mismatch
- Font anomalies
- Text overlap
- Layout inconsistencies

---

### 🔹 Image Forensics (No CNN)

File: forensic_image_detector.py

Replaced CNN with deterministic signals:

1. Noise Residual Analysis
2. JPEG Artifact Detection
3. Edge Inconsistency Detection

Final score:

score = 0.4 _ noise + 0.3 _ jpeg + 0.3 \* edge

Fully explainable and lightweight.

---

### 🔹 Feature Builder (Core)

File: feature_builder.py

Combines all signals into ML-ready features.

Key features:

- num_startxref
- time_gap_seconds
- stream_length_mismatch_count
- ocr_noise_weighted
- image_score_signature

---

### 🔹 Machine Learning

Models:

- Random Forest
- XGBoost
- Ensemble

Dataset:

```
dataset/
├── genuine/
├── tampered/
├── labels.csv
```

- Size: 296 samples
- Features: 34

---

## 🔥 Model Performance

| Model         | Accuracy | AUC    |
| ------------- | -------- | ------ |
| Random Forest | 88.33%   | 0.9417 |
| XGBoost       | 85.00%   | 0.9294 |
| Ensemble      | 93.33%   | 0.9439 |

---

## ⚙️ Ensemble Configuration

- XGBoost weight: 0.2
- Threshold: 0.4

---

## 🧠 Prediction Logic

Combined probability:
combined*prob = (0.2 * XGB) + (0.8 \_ RF)

Confidence:
confidence = abs(prob - threshold) / max(threshold, 1 - threshold)

Disagreement:
abs(RF - XGB)

---

## 🔍 Explainability (Domain-Based)

Example explanations:

- Multiple startxref sections detected
- Metadata inconsistency detected
- High OCR error rate
- Image compression anomaly

---

## 🧬 Tampering Types

- Text Tampering
- Image Tampering
- Metadata Tampering
- Structural Tampering

Each has a confidence score.

---

## 📊 API Endpoints

### Predict

POST /predict

Returns:

- Tampering probability
- Prediction
- Confidence
- Disagreement
- Tampering types
- Explanation

---

### Export Report

POST /export-report

Returns:

- Downloadable PDF forensic report

Includes:

- Summary
- Charts
- Explanation
- Raw output

---

## 💻 How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Start Backend (FastAPI)

```bash
uvicorn main:app --reload
```

Runs at:

```
http://localhost:8000
```

---

### 3. Start Frontend (Angular)

```bash
cd frontend
npm install
ng serve
```

Runs at:

```
http://localhost:4200
```

---

## 📄 Export Report

1. Upload PDF in UI
2. View analysis dashboard
3. Click "Export Report PDF"
4. Backend generates full forensic report

---

## 📊 Output Example

```json
{
  "tampering_probability": 0.91,
  "rf_probability": 0.88,
  "xgb_probability": 0.95,
  "prediction": "TAMPERED",
  "confidence": 0.85,
  "model_disagreement": 0.07,
  "tampering_types": [{ "type": "Structural Tampering", "confidence": 0.9 }],
  "explanation": [
    "Multiple startxref sections detected",
    "Stream mismatch detected"
  ]
}
```

---

## ⚠️ Limitations

- OCR noise possible
- Dataset size moderate
- Rule-based image detection (no deep learning)
- Some false positives

---

## 🚀 Future Work

- Larger dataset
- Advanced layout-aware models
- Improved visual tamper localization
- Cloud deployment

---

## 📌 Project Status

- Structural Analysis: Done
- Text Analysis: Done
- Image Forensics: Done
- Feature Engineering: Done
- ML Training: Done
- Explainability: Done
- UI Dashboard: Done
- PDF Export: Done

---

## 👨‍💻 Author

**Ayush Singh Rajput**
B.Tech CSE (2026), MNIT Jaipur

---

## 🧠 Key Achievement

Evolution:

```

Rule-based → Multi-modal → ML → Ensemble → Explainable System

```

Final Result:

**Production-ready PDF forensic analysis system**

```

```
