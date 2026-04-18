import os
import json
import uuid
import subprocess
import joblib
import numpy as np
import shap

from feature_builder import build_features, features_to_vector


# -------------------------------
# CONFIG
# -------------------------------
PIPELINE_SCRIPT = "run_full_pipeline.py"

rf_model = joblib.load("rf_model.pkl")
xgb_model = joblib.load("xgb_model.pkl")
config = joblib.load("ensemble_config.pkl")

WEIGHT_XGB = config["weight_xgb"]
THRESHOLD  = config["threshold"]
FEATURES   = config["features"]


# -------------------------------
# SHAP Explainer (Tree-based)
# -------------------------------
explainer = shap.TreeExplainer(rf_model)


# -------------------------------
# Risk Level
# -------------------------------
def get_risk_level(prob):
    if prob < 0.3:
        return "LOW"
    elif prob < 0.6:
        return "MEDIUM"
    else:
        return "HIGH"


# -------------------------------
# SHAP Explanation
# -------------------------------
def shap_explanation(features_vector):
    shap_values = explainer.shap_values(features_vector)

    values = shap_values[1][0]  # class 1 (tampered)

    contributions = list(zip(FEATURES, values))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    top = contributions[:5]

    explanation = []
    for name, val in top:
        if val > 0:
            explanation.append(f"{name} increased tampering likelihood")
        else:
            explanation.append(f"{name} reduced tampering likelihood")

    return explanation, contributions

def domain_explanation(features):
    reasons = []

    # Structural signals
    if features["num_startxref"] > 1:
        reasons.append("Multiple startxref sections (incremental update/tampering)")

    if features["stream_length_mismatch_count"] > 0:
        reasons.append("Mismatch between declared and actual stream lengths")

    if features["metadata_mismatch"] == 1:
        reasons.append("Metadata inconsistency (creator vs producer)")

    if features["time_gap_seconds"] > 1:
        reasons.append("Large creation-modification time gap")

    # OCR / layout signals
    if features["ocr_error_ratio"] > 0.2:
        reasons.append("High OCR error rate")

    if features["overlap_density"] > 0.3:
        reasons.append("High text overlap density")

    if features["font_anomaly_ratio"] > 0.2:
        reasons.append("Font inconsistencies detected")

    if features["max_local_overlap"] > 20:
        reasons.append("Extreme localized overlap")

    # Combined signals
    if features["tamper_signal"] > 2:
        reasons.append("Strong combined tampering signal")

    if features["tri_modal_conflict"] > 1:
        reasons.append("Conflict across structure, image, and text layers")

    return reasons

def hybrid_explanation(features, features_vector):
    shap_exp, contributions = shap_explanation(features_vector)
    domain_exp = domain_explanation(features)

    # Convert top SHAP features into set
    top_shap_features = {name for name, _ in contributions[:7]}

    # Map feature → domain meaning (important!)
    feature_to_reason = {
        "num_startxref": "Multiple startxref sections",
        "stream_length_mismatch_count": "Stream length mismatch",
        "metadata_mismatch": "Metadata inconsistency",
        "time_gap_seconds": "Creation-modification time gap",
        "ocr_error_ratio": "High OCR error",
        "overlap_density": "High overlap density",
        "font_anomaly_ratio": "Font anomaly",
        "max_local_overlap": "Extreme overlap",
        "tamper_signal": "Strong tampering signal",
        "tri_modal_conflict": "Cross-layer conflict",
    }

    aligned_reasons = []

    # Keep domain reasons that align with SHAP-important features
    for feature, desc in feature_to_reason.items():
        if feature in top_shap_features:
            for reason in domain_exp:
                if desc.lower() in reason.lower():
                    aligned_reasons.append(reason)

    # Final merge strategy
    final_explanation = []

    # Priority 1: aligned reasons (best quality)
    final_explanation.extend(aligned_reasons[:3])

    # Priority 2: remaining SHAP explanations
    for exp in shap_exp:
        if len(final_explanation) >= 5:
            break
        final_explanation.append(exp)

    # Fallback
    if not final_explanation:
        final_explanation = shap_exp[:3]

    return final_explanation

# -------------------------------
# Prediction
# -------------------------------
def predict_pdf(pdf_path):
    job_id = uuid.uuid4().hex[:12]

    final_output_file = f"final_output_{job_id}.json"
    text_output_file  = f"text_output_{job_id}.json"
    struct_file = f"{pdf_path}.{job_id}.features.json"

    try:
        subprocess.run(
            ["python", PIPELINE_SCRIPT, pdf_path, "False", job_id],
            check=False
        )

        if not os.path.exists(final_output_file) or not os.path.exists(text_output_file):
            raise Exception("Pipeline failed")

        with open(final_output_file) as f:
            final_data = json.load(f)

        with open(text_output_file) as f:
            text_data = json.load(f)

        # -------------------------------
        # Build features
        # -------------------------------
        features = build_features(final_data, text_data, struct_file)
        X = np.array([features_to_vector(features)])

        # -------------------------------
        # Model prediction
        # -------------------------------
        rf_prob  = rf_model.predict_proba(X)[0][1]
        xgb_prob = xgb_model.predict_proba(X)[0][1]

        combined_prob = (
            WEIGHT_XGB * xgb_prob +
            (1 - WEIGHT_XGB) * rf_prob
        )

        prediction = int(combined_prob > THRESHOLD)

        # -------------------------------
        # SHAP Explanation
        # -------------------------------
        explanation = hybrid_explanation(features, X)

        result = {
            "pdf": os.path.basename(pdf_path),
            "tampering_probability": round(float(combined_prob), 4),
            "prediction": "TAMPERED" if prediction == 1 else "GENUINE",
            "risk_level": get_risk_level(combined_prob),
            "explanation": explanation
        }

        return result

    finally:
        for path in [
            final_output_file,
            text_output_file,
            struct_file,
            f"image_output_{job_id}.json",
        ]:
            try:
                os.remove(path)
            except:
                pass


# -------------------------------
# CLI
# -------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python predict.py <pdf_path>")
        exit(1)

    pdf_path = sys.argv[1]

    result = predict_pdf(pdf_path)

    print("\n🔍 PDF Analysis Result\n")
    print(json.dumps(result, indent=4))