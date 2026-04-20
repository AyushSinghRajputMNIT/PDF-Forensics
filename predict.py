import os
import json
import uuid
import subprocess
import joblib
import numpy as np

from feature_builder import build_features, features_to_vector


# -------------------------------
# CONFIG
# -------------------------------
PIPELINE_SCRIPT = "run_full_pipeline.py"

rf_model = joblib.load("rf_model_with_img.pkl")
xgb_model = joblib.load("xgb_model_with_img.pkl")
config = joblib.load("ensemble_config_with_img.pkl")

WEIGHT_XGB = config["weight_xgb"]
THRESHOLD  = config["threshold"]
FEATURES   = config["features"]


# -------------------------------
# SAME NORMALIZATION AS TRAINING
# -------------------------------
def apply_feature_transforms(features_dict):
    log_features = [
        "overlap_severity",
        "max_local_overlap",
        "time_gap_seconds",
        "stream_length_mismatch_count"
    ]

    for col in log_features:
        if col in features_dict:
            features_dict[col] = np.log1p(features_dict[col])

    # Clip values
    for k in features_dict:
        features_dict[k] = np.clip(features_dict[k], -10, 10)

    return features_dict


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
# Domain Explanation (NO SHAP)
# -------------------------------
def domain_explanation(features):
    reasons = []

    # Structural
    if features["num_startxref"] > 1:
        reasons.append("Multiple startxref sections (possible incremental tampering)")

    if features["stream_length_mismatch_count"] > 0:
        reasons.append("Mismatch between declared and actual stream lengths")

    if features["metadata_mismatch"] == 1:
        reasons.append("Metadata inconsistency detected")

    if features["time_gap_seconds"] > 1:
        reasons.append("Large creation-modification time gap")

    # Image
    if features["avg_ela_variance"] > 0.05:
        reasons.append("High image compression inconsistency (ELA anomaly)")

    if features["image_score_signature"] > 0.5:
        reasons.append("Suspicious signature region detected")

    if features["image_score_stamp"] > 0.5:
        reasons.append("Suspicious stamp region detected")

    # Text
    if features["ocr_error_ratio"] > 0.2:
        reasons.append("High OCR error rate")

    if features["overlap_density"] > 0.3:
        reasons.append("High text overlap density")

    if features["font_anomaly_ratio"] > 0.2:
        reasons.append("Font inconsistencies detected")

    if features["max_local_overlap"] > 20:
        reasons.append("Extreme localized text overlap")

    # Combined
    if features["struct_text_conflict"] > 0.2:
        reasons.append("Conflict between structure and text layers")

    if features["image_text_conflict"] > 0.2:
        reasons.append("Conflict between image and text layers")

    if features["cleanliness_score"] < 0:
        reasons.append("Low document cleanliness score")

    return reasons[:5]  # limit output


# -------------------------------
# Prediction
# -------------------------------
def predict_pdf(pdf_path):
    job_id = uuid.uuid4().hex[:12]

    final_output_file = f"final_output_{job_id}.json"
    text_output_file  = f"text_output_{job_id}.json"
    image_output_file = f"image_output_{job_id}.json"
    struct_file = f"{pdf_path}.{job_id}.features.json"

    try:
        subprocess.run(
            ["python", PIPELINE_SCRIPT, pdf_path, "False", job_id],
            check=False
        )

        if not (
            os.path.exists(final_output_file) and
            os.path.exists(text_output_file) and
            os.path.exists(image_output_file)
        ):
            raise Exception("Pipeline failed")

        with open(final_output_file) as f:
            final_data = json.load(f)

        with open(text_output_file) as f:
            text_data = json.load(f)

        with open(image_output_file) as f:
            image_data = json.load(f)

        # -------------------------------
        # Build features
        # -------------------------------
        features = build_features(
            final_data=final_data,
            text_data=text_data,
            image_data=image_data,
            struct_json_path=struct_file
        )

        # 🔥 APPLY SAME TRANSFORM AS TRAINING
        features = apply_feature_transforms(features)

        X = np.array([features_to_vector(features)])

        # -------------------------------
        # Ensemble prediction
        # -------------------------------
        rf_prob  = rf_model.predict_proba(X)[0][1]
        xgb_prob = xgb_model.predict_proba(X)[0][1]

        combined_prob = (
            WEIGHT_XGB * xgb_prob +
            (1 - WEIGHT_XGB) * rf_prob
        )

        prediction = int(combined_prob > THRESHOLD)

        # -------------------------------
        # Explanation (domain only)
        # -------------------------------
        explanation = domain_explanation(features)

        result = {
            "pdf": os.path.basename(pdf_path),
            "tampering_probability": round(float(combined_prob), 4),
            "rf_probability": round(float(rf_prob), 4),
            "xgb_probability": round(float(xgb_prob), 4),
            "prediction": "TAMPERED" if prediction == 1 else "GENUINE",
            "risk_level": get_risk_level(combined_prob),
            "explanation": explanation
        }

        return result

    finally:
        for path in [
            final_output_file,
            text_output_file,
            image_output_file,
            struct_file,
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