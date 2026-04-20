import numpy as np
import cv2
from PIL import Image

# =========================================================
# 1. NOISE RESIDUAL ANALYSIS (PRNU-like)
# =========================================================
def noise_residual_score(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0

        img = img.astype(np.float32)

        # Simple denoising (approx expected content)
        denoised = cv2.GaussianBlur(img, (5, 5), 0)

        residual = img - denoised

        # variance of residual = noise inconsistency
        score = np.var(residual)

        # normalize (empirical scaling)
        return float(min(score / 1000.0, 1.0))

    except:
        return 0.0


# =========================================================
# 2. JPEG ARTIFACT DETECTION (DCT inconsistency proxy)
# =========================================================
def jpeg_artifact_score(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return 0.0

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        h, w = gray.shape

        # block-based variance (JPEG 8x8 assumption)
        block_size = 8
        scores = []

        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                scores.append(np.std(block))

        if len(scores) == 0:
            return 0.0

        block_var = np.mean(scores)

        # high variance inconsistency = possible recompression/tamper
        return float(min(block_var / 50.0, 1.0))

    except:
        return 0.0


# =========================================================
# 3. EDGE INCONSISTENCY SCORE
# =========================================================
def edge_inconsistency_score(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0

        edges = cv2.Canny(img, 50, 150)

        h, w = edges.shape
        if h == 0 or w == 0:
            return 0.0

        # split into patches
        patch_size = 32
        scores = []

        for y in range(0, h - patch_size, patch_size):
            for x in range(0, w - patch_size, patch_size):
                patch = edges[y:y+patch_size, x:x+patch_size]
                scores.append(np.mean(patch))

        if len(scores) == 0:
            return 0.0

        # inconsistency = variance across patches
        return float(min(np.var(scores) * 5, 1.0))

    except:
        return 0.0


# =========================================================
# FINAL COMBINED FEATURE
# =========================================================
def predict_tampering(image_path):
    """
    Replaces CNN completely.
    Returns a forensic tamper probability score.
    """

    noise = noise_residual_score(image_path)
    jpeg = jpeg_artifact_score(image_path)
    edge = edge_inconsistency_score(image_path)

    # Weighted fusion (tunable)
    score = (
        0.4 * noise +
        0.3 * jpeg +
        0.3 * edge
    )

    return float(min(score, 1.0))