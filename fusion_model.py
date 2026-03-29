def compute_textual_score(text_features):
    score = 0

    if text_features["ocr_similarity"] < 0.8:
        score += 0.3
    if text_features["ocr_mismatch_count"] > 10:
        score += 0.2
    if text_features["baseline_anomaly_count"] > 5:
        score += 0.2
    if text_features["font_anomaly"] > 0:
        score += 0.2

    return min(score, 1.0)


def compute_image_score(image_features):
    if not image_features:
        return 0.0

    score = 0

    if image_features["avg_ela_variance"] > 15:
        score += 0.4
    elif image_features["avg_ela_variance"] > 8:
        score += 0.2

    if image_features["avg_cnn_tamper_prob"] > 0.2:
        score += 0.3
    elif image_features["avg_cnn_tamper_prob"] > 0.1:
        score += 0.1

    return min(score, 1.0)


def fuse_scores(struct_score, text_score, image_score):
    w_struct = 0.4
    w_text = 0.35
    w_image = 0.25

    return (
        w_struct * struct_score +
        w_text * text_score +
        w_image * image_score
    )


def classify(score):
    if score < 0.2:
        return "CLEAN"
    elif score < 0.4:
        return "MINOR_ANOMALY"
    elif score < 0.6:
        return "SUSPICIOUS"
    elif score < 0.8:
        return "LIKELY_TAMPERED"
    else:
        return "HIGHLY_TAMPERED"