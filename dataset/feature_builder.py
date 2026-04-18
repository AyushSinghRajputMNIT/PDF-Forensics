import json
import os


# -------------------------------
# Feature List (single source of truth)
# -------------------------------
FEATURE_COLUMNS = [
    "struct_score",
    "image_score",

    "ocr_similarity",
    "ocr_error_ratio",
    "font_anomaly_ratio",
    "overlap_density",
    "max_local_overlap",

    "overlap_severity",
    "ocr_layout_mismatch",
    "font_ocr_mix",
    "normalized_overlap",
    "relative_ocr_drop",

    "struct_text_conflict",
    "image_text_conflict",
    "ocr_noise_weighted",
    "extreme_overlap_flag",
    "cleanliness_score",

    "tamper_signal",
    "tamper_ratio",

    # Structural
    "num_startxref",
    "objects_with_multiple_revisions",
    "stream_length_mismatch_count",
    "metadata_mismatch",
    "time_gap_seconds",

    # Cross-modal
    "tri_modal_conflict",
]


# -------------------------------
# MAIN FEATURE BUILDER
# -------------------------------
def build_features(final_data, text_data, struct_json_path=None):
    """
    final_data: output of final_output.json
    text_data: output of text_output.json
    struct_json_path: path to structural features JSON
    """

    # -------------------------------
    # Base Features
    # -------------------------------
    struct_score = final_data.get("structural_score", 0)
    image_score  = final_data.get("image_score", 0)

    ocr_similarity     = text_data.get("ocr_similarity", 1.0)
    ocr_error_ratio    = text_data.get("ocr_error_ratio", 0)
    font_anomaly_ratio = text_data.get("font_anomaly_ratio", 0)
    overlap_density    = text_data.get("overlap_density", 0)
    max_local_overlap  = text_data.get("max_local_overlap", 0)

    # -------------------------------
    # Derived Features
    # -------------------------------
    overlap_severity    = overlap_density * max_local_overlap
    ocr_layout_mismatch = ocr_error_ratio * overlap_density
    font_ocr_mix        = font_anomaly_ratio * ocr_error_ratio

    normalized_overlap = overlap_density / (1 + max_local_overlap)
    relative_ocr_drop  = 1 - ocr_similarity

    # -------------------------------
    # Strong Features
    # -------------------------------
    struct_text_conflict = abs(struct_score - (1 - ocr_similarity))
    image_text_conflict  = abs(image_score - (1 - ocr_similarity))
    ocr_noise_weighted   = ocr_error_ratio * (1 + overlap_density)
    extreme_overlap_flag = 1 if max_local_overlap > 20 else 0
    cleanliness_score    = ocr_similarity * (1 - overlap_density)

    tri_modal_conflict = (
        abs(struct_score - image_score) +
        abs(image_score - (1 - ocr_similarity))
    )

    tamper_signal = (
        2.5 * ocr_error_ratio +
        2.0 * overlap_density +
        1.5 * (max_local_overlap / 10) +
        1.5 * font_anomaly_ratio +
        2.0 * (1 - ocr_similarity) +
        1.5 * struct_text_conflict +
        1.0 * image_text_conflict
    )

    tamper_ratio = tamper_signal / (1 + struct_score + image_score)

    # -------------------------------
    # Structural Features
    # -------------------------------
    num_startxref = 0
    objects_with_multiple_revisions = 0
    stream_length_mismatch_count = 0
    metadata_mismatch = 0
    time_gap_seconds = 0

    if struct_json_path and os.path.exists(struct_json_path):
        try:
            with open(struct_json_path) as f:
                struct_json = json.load(f)

            num_startxref = struct_json.get("num_startxref", 0)

            objects_with_multiple_revisions = struct_json.get(
                "objects", {}
            ).get("objects_with_multiple_revisions", 0)

            stream_length_mismatch_count = struct_json.get(
                "streams", {}
            ).get("stream_length_mismatch_count", 0)

            metadata_mismatch = int(
                struct_json.get("metadata_mismatch_creator_producer", False)
            )

            time_gap_seconds = struct_json.get(
                "metadata", {}
            ).get("creation_modification_time_gap_seconds", 0)

            if time_gap_seconds is None:
                time_gap_seconds = 0

            # -------------------------------
            # Normalization
            # -------------------------------
            time_gap_seconds = min(time_gap_seconds / 86400, 365)
            num_startxref = min(num_startxref, 10)
            objects_with_multiple_revisions = min(objects_with_multiple_revisions, 20)
            stream_length_mismatch_count = min(stream_length_mismatch_count, 50)

        except Exception as e:
            print(f"[STRUCT ERROR] {struct_json_path}: {e}")

    # -------------------------------
    # Final Feature Dict
    # -------------------------------
    features = {
        "struct_score": struct_score,
        "image_score": image_score,

        "ocr_similarity": ocr_similarity,
        "ocr_error_ratio": ocr_error_ratio,
        "font_anomaly_ratio": font_anomaly_ratio,
        "overlap_density": overlap_density,
        "max_local_overlap": max_local_overlap,

        "overlap_severity": overlap_severity,
        "ocr_layout_mismatch": ocr_layout_mismatch,
        "font_ocr_mix": font_ocr_mix,
        "normalized_overlap": normalized_overlap,
        "relative_ocr_drop": relative_ocr_drop,

        "struct_text_conflict": struct_text_conflict,
        "image_text_conflict": image_text_conflict,
        "ocr_noise_weighted": ocr_noise_weighted,
        "extreme_overlap_flag": extreme_overlap_flag,
        "cleanliness_score": cleanliness_score,

        "tamper_signal": tamper_signal,
        "tamper_ratio": tamper_ratio,

        "num_startxref": num_startxref,
        "objects_with_multiple_revisions": objects_with_multiple_revisions,
        "stream_length_mismatch_count": stream_length_mismatch_count,
        "metadata_mismatch": metadata_mismatch,
        "time_gap_seconds": time_gap_seconds,

        "tri_modal_conflict": tri_modal_conflict,
    }

    return features


# -------------------------------
# Utility: Convert to model vector
# -------------------------------
def features_to_vector(features):
    return [features.get(col, 0) for col in FEATURE_COLUMNS]