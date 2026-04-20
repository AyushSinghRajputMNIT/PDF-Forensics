import os
import json
import uuid
import subprocess
import joblib
import numpy as np
import pandas as pd

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
    if prob < THRESHOLD - 0.1:
        return("LOW")
    elif prob < THRESHOLD + 0.1:
        return("MEDIUM")
    else:
        return("HIGH")


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

def compute_confidence(prob, threshold):
    if prob >= threshold:
        # Confidence for TAMPERED
        return (prob - threshold) / (1 - threshold)
    else:
        # Confidence for GENUINE
        return (threshold - prob) / threshold
    
def compute_disagreement_level(d):
    if d < 0.1:
        return "LOW"
    elif d < 0.3:
        return "MEDIUM"
    else:
        return "HIGH"
    
def get_final_decision(prob, confidence, disagreement):
    if confidence < 0.15 or disagreement > 0.3:
        return "UNCERTAIN"

    return "TAMPERED" if prob > THRESHOLD else "GENUINE"

# -------------------------------
# Tampering Type Detection (with confidence)
# -------------------------------
def detect_tampering_types(features):
    scores = {
        "Text Tampering": 0.0,
        "Image Tampering": 0.0,
        "Metadata Tampering": 0.0,
        "Structural Tampering": 0.0
    }

    # -------------------------------
    # TEXT TAMPERING
    # -------------------------------
    scores["Text Tampering"] += min(features.get("ocr_error_ratio", 0) * 2, 1.0)
    scores["Text Tampering"] += min(features.get("overlap_density", 0), 1.0)
    scores["Text Tampering"] += min(features.get("font_anomaly_ratio", 0), 1.0)

    # -------------------------------
    # IMAGE TAMPERING
    # -------------------------------
    scores["Image Tampering"] += min(features.get("image_score_signature", 0), 1.0)
    scores["Image Tampering"] += min(features.get("image_score_stamp", 0), 1.0)
    scores["Image Tampering"] += min(features.get("image_score_logo", 0), 1.0)
    scores["Image Tampering"] += min(features.get("image_score_internal", 0), 1.0)
    scores["Image Tampering"] += min(features.get("avg_ela_variance", 0), 1.0)

    # -------------------------------
    # METADATA TAMPERING
    # -------------------------------
    if features.get("metadata_mismatch", 0) == 1:
        scores["Metadata Tampering"] += 1.0

    scores["Metadata Tampering"] += min(features.get("time_gap_seconds", 0) / 10, 1.0)

    # -------------------------------
    # STRUCTURAL TAMPERING
    # -------------------------------
    if features.get("num_startxref", 0) > 1:
        scores["Structural Tampering"] += 1.0

    scores["Structural Tampering"] += min(features.get("stream_length_mismatch_count", 0), 1.0)

    # -------------------------------
    # Normalize scores → confidence
    # -------------------------------
    max_score = max(scores.values()) if max(scores.values()) > 0 else 1.0

    results = []
    for k, v in scores.items():
        conf = round(v / max_score, 3)

        # Filter weak signals
        if conf > 0.2:
            results.append({
                "type": k,
                "confidence": conf
            })

    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)

    return results

def generate_case_summary(types, disagreement_level):
    if not types:
        return "No strong tampering signals detected."

    primary = types[0]["type"]
    summary = f"Primary signal: {primary}"

    if len(types) > 1:
        secondary = types[1]["type"]
        summary += f", with supporting evidence of {secondary.lower()}."

    if disagreement_level == "HIGH":
        summary += " However, high model disagreement suggests uncertain or partial tampering."

    elif disagreement_level == "MEDIUM":
        summary += " Some model disagreement observed."

    return summary

def get_forensic_verdict(prediction, disagreement_level):
    if prediction == "GENUINE":
        return "No significant evidence of tampering"

    if prediction == "TAMPERED" and disagreement_level == "LOW":
        return "Strong evidence of tampering"

    if prediction == "TAMPERED":
        return "Moderate evidence of tampering"

    return "Inconclusive evidence of tampering"

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

        # Align features strictly with training
        vector = [features.get(f, 0) for f in FEATURES]
        X = pd.DataFrame([vector], columns=FEATURES)

        # -------------------------------
        # Ensemble prediction
        # -------------------------------
        rf_prob  = rf_model.predict_proba(X)[0][1]
        xgb_prob = xgb_model.predict_proba(X)[0][1]

        combined_prob = (
            WEIGHT_XGB * xgb_prob +
            (1 - WEIGHT_XGB) * rf_prob
        )

        model_disagreement = abs(rf_prob - xgb_prob)
        disagreement_level = compute_disagreement_level(model_disagreement)
        confidence = compute_confidence(combined_prob, THRESHOLD)

        raw_prediction = int(combined_prob > THRESHOLD)
        final_decision = get_final_decision(combined_prob, confidence, model_disagreement)

        # -------------------------------
        # Explanation (domain only)
        # -------------------------------
        explanation = domain_explanation(features)
        tampering_types = detect_tampering_types(features)
        case_summary = generate_case_summary(tampering_types, disagreement_level)
        confidence = abs(combined_prob - THRESHOLD) / max(THRESHOLD, 1 - THRESHOLD)

        result = {
            "pdf": os.path.basename(pdf_path),
            "tampering_probability": round(float(combined_prob), 4),
            "rf_probability": round(float(rf_prob), 4),
            "xgb_probability": round(float(xgb_prob), 4),
            "prediction": final_decision,
            "model_prediction": "TAMPERED" if raw_prediction == 1 else "GENUINE",
            "risk_level": get_risk_level(combined_prob),
            "confidence": round(confidence, 3),
            "model_disagreement": round(float(model_disagreement), 4),
            "disagreement_level": disagreement_level,
            "tampering_types": tampering_types,
            "case_summary": case_summary,
            "forensic_verdict": get_forensic_verdict(final_decision, disagreement_level),
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