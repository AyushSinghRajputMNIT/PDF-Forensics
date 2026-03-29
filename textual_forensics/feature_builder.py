def build_text_features(layout, ocr, font):
    return {
        "baseline_std": layout.get("baseline_std", 0),
        "baseline_anomaly_count": layout.get("baseline_anomaly_count", 0),
        "ocr_similarity": ocr.get("ocr_avg_similarity", 1.0),
        "ocr_mismatch_count": ocr.get("ocr_mismatch_count", 0),
        "font_entropy": font.get("font_entropy", 0),
        "font_count": font.get("font_count", 0),
        "font_anomaly": int(font.get("font_anomaly", False))
    }