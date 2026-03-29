from .ela_analysis import compute_ela
from .cnn_detector import predict_tampering

def extract_image_features(image_paths):
    print("\n[2/3] Analyzing extracted images...")

    features = []
    total = len(image_paths)

    if total == 0:
        print("   ⚠ No images found in PDF\n")
        return {}

    for i, path in enumerate(image_paths):
        progress = (i + 1) / total * 100
        print(f"\n   → Image {i+1}/{total} ({progress:.1f}%)")

        ela = compute_ela(path)
        cnn_score = predict_tampering(path)

        features.append({
            "image_path": path,
            "ela_mean": ela["ela_mean"],
            "ela_variance": ela["ela_variance"],
            "ela_high_pixels": ela["ela_high_pixels"],
            "cnn_tamper_prob": cnn_score
        })

    print("\n   ✔ Image analysis completed\n")

    avg_ela_var = sum(f["ela_variance"] for f in features) / total
    avg_cnn = sum(f["cnn_tamper_prob"] for f in features) / total

    return {
        "num_images": total,
        "avg_ela_variance": avg_ela_var,
        "avg_cnn_tamper_prob": avg_cnn,
        "images": features
    }