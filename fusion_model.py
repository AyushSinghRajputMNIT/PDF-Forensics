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

    noise = image_features.get("avg_noise_residual_score", 0)
    jpeg  = image_features.get("avg_jpeg_artifact_score", 0)
    edge  = image_features.get("avg_edge_inconsistency_score", 0)
    ela   = image_features.get("avg_ela_variance", 0)

    score = 0

    if ela > 15:
        score += 0.3
    elif ela > 8:
        score += 0.15

    if noise > 0.15:
        score += 0.25

    if jpeg > 0.15:
        score += 0.2

    if edge > 0.15:
        score += 0.2

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