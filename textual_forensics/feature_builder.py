def build_text_features(layout, ocr, font):
    word_count = max(layout.get("word_count", 1), 1)

    overlap_count = layout.get("overlap_count", 0)
    overlap_density = overlap_count / word_count
    max_local_overlap = layout.get("max_local_overlap", 0)

    font_anomaly = font.get("font_anomaly", 0)
    font_anomaly_ratio = font_anomaly / word_count

    ocr_mismatch = ocr.get("ocr_mismatch_count", 0)
    ocr_error_ratio = ocr_mismatch / word_count

    # -------------------------------
    # 🔥 NEW INTERACTION FEATURES
    # -------------------------------

    overlap_severity = overlap_density * max_local_overlap

    ocr_layout_mismatch = ocr_error_ratio * overlap_density

    font_ocr_mix = font_anomaly_ratio * ocr_error_ratio

    return {
        # -------------------------------
        # Core Features
        # -------------------------------
        "baseline_anomaly_count": layout.get("baseline_anomaly_count", 0),

        "ocr_similarity": ocr.get("ocr_similarity", 1.0),
        "ocr_mismatch_count": ocr_mismatch,

        "font_entropy": font.get("font_entropy", 0),
        "font_count": font.get("font_count", 0),
        "font_anomaly": int(font.get("font_anomaly", False)),

        # -------------------------------
        # Layout Features
        # -------------------------------
        "overlap_count": overlap_count,
        "overlap_density": overlap_density,
        "max_local_overlap": max_local_overlap,
        "word_count": word_count,

        # -------------------------------
        # Ratio Features
        # -------------------------------
        "font_anomaly_ratio": font_anomaly_ratio,
        "ocr_error_ratio": ocr_error_ratio,

        # -------------------------------
        # 🔥 Interaction Features (KEY)
        # -------------------------------
        "overlap_severity": overlap_severity,
        "ocr_layout_mismatch": ocr_layout_mismatch,
        "font_ocr_mix": font_ocr_mix
    }

