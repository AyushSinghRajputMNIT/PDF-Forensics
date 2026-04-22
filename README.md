# 🕵️ PDF Forgery Detection using Multi-Modal Forensics + ML

### B.Tech CSE Major Project

This project implements a **production-grade PDF forensics system** that detects document tampering using **multi-modal analysis + machine learning + explainability**.

It analyzes PDFs across multiple layers:

- 📄 Structural (low-level PDF internals)
- 📝 Textual (OCR, fonts, layout consistency)
- 🖼️ Image (forensic signal analysis — no CNN)
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
- Train ML models (RF + XGBoost)
- Provide **industry-level explainability (SHAP + domain logic)**
- Generate **forensic PDF reports with charts**

---

## ⚙️ System Architecture

```
INPUT PDF
   │
   ├── Structural Analysis
   ├── Textual Analysis
   ├── Image Forensics (Signal-based)
   │
   └── Feature Builder
            │
      ML Models (RF + XGB)
            │
   Probability + Risk + Confidence
            │
   Explainability Engine (SHAP + Rules)
            │
        Final Output + Report
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

📌 **Strongest tampering signal**

---

### 🔹 Textual Analysis

- Extracts embedded text + fonts
- Performs OCR using Tesseract
- Compares OCR vs embedded text

Detects:

- OCR mismatch
- Font anomalies
- Layout inconsistencies
- Overlapping text

📌 OCR skipped for large PDFs for performance

---

### 🔹 Image Forensics (NEW — No CNN)

Replaced deep learning CNN with **interpretable forensic signals**

File: `forensic_image_detector.py`

#### Signals Used:

**1. Noise Residual Analysis**

- Detects unnatural noise patterns
- Proxy for PRNU inconsistency

**2. JPEG Artifact Detection**

- Detects recompression artifacts
- Uses block-level variance (8x8)

**3. Edge Inconsistency**

- Detects unnatural edge distribution
- Identifies patch-level irregularities

#### Final Score:

```
score = 0.4 * noise + 0.3 * jpeg + 0.3 * edge
```

📌 Benefits:

- No heavy GPU dependency
- Fully explainable
- Faster inference
- More stable for documents

---

### 🔹 Feature Builder (🔥 CORE)

File: `feature_builder.py`

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

**Structural Features**

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

Why two models?

- Capture different patterns
- Reduce bias
- Enable disagreement-based confidence

---

### 🔹 Confidence & Disagreement

**Confidence is computed using:**

- Model agreement (RF vs XGB)
- Signal consistency
- Feature stability
- Strength of tampering indicators

**Disagreement:**

```
|RF - XGB|
```

📌 High disagreement = uncertain prediction

---

### 🔹 Explainability Engine

File: `predict.py`

Includes:

1. **SHAP values** → feature contribution
2. **Domain logic** → human-readable reasoning
3. **Hybrid explanation output**

Example:

- HIGH: Multiple xref sections detected
- MEDIUM: OCR inconsistency
- LOW: Image anomalies

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

Supports:

- Resume
- Parallel execution
- Retry handling

---

## 🤖 Model Performance

| Model         | Accuracy |
| ------------- | -------- |
| Random Forest | 88.33%   |
| XGBoost       | 85.00%   |

📌 RF performs best in most cases

---

## 📄 PDF Report Export (Backend)

Reports include:

- File metadata
- Verdict & risk
- Confidence score
- 📊 Charts:
  - Model comparison (bar)
  - Confidence (doughnut)
  - Tampering types (radar)
- Explanation
- Raw JSON output

---

## ▶️ How to Run

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

### 4. Use the Application

1. Upload a PDF
2. View forensic analysis dashboard
3. Inspect:
   - Charts
   - Confidence
   - Explanation
4. Click **Export Report**
5. Download full forensic PDF report

---

## 📊 Sample Output

```json
{
  "tampering_probability": 0.78,
  "prediction": "TAMPERED",
  "risk_level": "HIGH",
  "confidence": 0.82,
  "model_disagreement": 0.12,
  "tampering_types": [
    { "type": "Text Tampering", "confidence": 0.9 },
    { "type": "Metadata Tampering", "confidence": 0.6 }
  ],
  "explanation": ["Multiple xref sections detected", "OCR inconsistency found"]
}
```

---

## ⚠️ Limitations

- OCR noise in low-quality scans
- Dataset size moderate
- Some borderline false positives

---

## 🚀 Future Work

- Layout-aware models (LayoutLM)
- Tamper heatmaps
- Larger dataset
- Real-time API scaling
- Advanced PDF attack detection

---

## 📌 Project Status

| Component           | Status            |
| ------------------- | ----------------- |
| Structural Analysis | ✅                |
| Textual Analysis    | ✅                |
| Image Forensics     | ✅ (signal-based) |
| Feature Engineering | ✅                |
| ML Models           | ✅                |
| Explainability      | ✅                |
| Frontend UI         | ✅                |
| PDF Export          | ✅                |

---

## 👨‍💻 Author

**Ayush Singh Rajput**  
B.Tech CSE (2026), MNIT Jaipur

---

## 🧠 Key Achievement

Evolution:

```
Rule-based → Multi-modal → ML → Explainable AI → Production System
```

👉 Result: **Robust, interpretable PDF forensic detection system**
