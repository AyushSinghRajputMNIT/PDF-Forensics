from .ela_analysis import compute_ela
from .forensic_image_detector import (
    noise_residual_score,
    jpeg_artifact_score,
    edge_inconsistency_score
)

import numpy as np


def extract_image_features(images_meta):
    print("\n[IMAGE ANALYSIS] Processing...")

    features = []

    noise_scores = []
    jpeg_scores = []
    edge_scores = []

    for i, img in enumerate(images_meta):

        path = img["path"]
        img_type = img.get("type", "unknown")
        source = img.get("source", "rendered")

        print(f" → {i+1}/{len(images_meta)} [{img_type}, {source}]")

        # ELA (still useful)
        ela = compute_ela(path)

        # 🔥 forensic components (replacing CNN)
        noise = noise_residual_score(path)
        jpeg  = jpeg_artifact_score(path)
        edge  = edge_inconsistency_score(path)

        # type bias (your idea is good — keep it)
        type_bias = {
            "signature": 1.2,
            "stamp": 1.0,
            "logo": 0.8,
            "unknown": 1.0
        }.get(img_type, 1.0)

        noise *= type_bias
        jpeg  *= type_bias
        edge  *= type_bias

        noise_scores.append(noise)
        jpeg_scores.append(jpeg)
        edge_scores.append(edge)

        features.append({
            "image_path": path,
            "type": img_type,
            "source": source,

            # ELA features
            "ela_mean": ela["ela_mean"],
            "ela_variance": ela["ela_variance"],
            "ela_high_pixels": ela["ela_high_pixels"],

            # forensic decomposition (NEW)
            "noise_residual_score": noise,
            "jpeg_artifact_score": jpeg,
            "edge_inconsistency_score": edge
        })

    # -------------------------------
    # Aggregated image-level features
    # -------------------------------
    return {
        "num_images": len(features),

        # ELA aggregate
        "avg_ela_variance": float(np.mean([f["ela_variance"] for f in features])),

        # forensic aggregates (REPLACING CNN)
        "avg_noise_residual_score": float(np.mean(noise_scores)) if noise_scores else 0,
        "avg_jpeg_artifact_score": float(np.mean(jpeg_scores)) if jpeg_scores else 0,
        "avg_edge_inconsistency_score": float(np.mean(edge_scores)) if edge_scores else 0,

        # full breakdown
        "images": features
    }