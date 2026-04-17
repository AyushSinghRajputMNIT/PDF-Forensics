import numpy as np

def compute_overlap_count(spans, min_overlap_ratio=0.3):
    overlap_count = 0

    for i in range(len(spans)):
        x0_i, y0_i, x1_i, y1_i = spans[i]["bbox"]
        area_i = (x1_i - x0_i) * (y1_i - y0_i)

        for j in range(i + 1, len(spans)):
            x0_j, y0_j, x1_j, y1_j = spans[j]["bbox"]

            # Intersection box
            xi0 = max(x0_i, x0_j)
            yi0 = max(y0_i, y0_j)
            xi1 = min(x1_i, x1_j)
            yi1 = min(y1_i, y1_j)

            if xi1 > xi0 and yi1 > yi0:
                inter_area = (xi1 - xi0) * (yi1 - yi0)

                # Normalize by smaller box
                min_area = min(area_i, (x1_j - x0_j) * (y1_j - y0_j))

                overlap_ratio = inter_area / max(min_area, 1)

                if overlap_ratio > min_overlap_ratio:
                    overlap_count += 1

    return overlap_count

def compute_max_local_overlap(spans, window_size=50):
    max_overlap = 0

    for i in range(len(spans)):
        x0_i, y0_i, x1_i, y1_i = spans[i]["bbox"]

        local_count = 0

        for j in range(len(spans)):
            x0_j, y0_j, x1_j, y1_j = spans[j]["bbox"]

            # Nearby region check
            if abs(x0_i - x0_j) < window_size and abs(y0_i - y0_j) < window_size:
                # overlap check
                if not (x1_i < x0_j or x1_j < x0_i or y1_i < y0_j or y1_j < y0_i):
                    local_count += 1

        max_overlap = max(max_overlap, local_count)

    return max_overlap

def compute_spacing_variance(baselines):
    if len(baselines) < 2:
        return 0

    ys = sorted(baselines)
    gaps = [ys[i+1] - ys[i] for i in range(len(ys)-1)]

    if not gaps:
        return 0

    return float(np.var(gaps))


def analyze_layout(spans):
    print("\n[2/4] Performing layout analysis...")

    baselines = []
    total = len(spans)

    for i, span in enumerate(spans):
        if i % max(1, total // 10) == 0:
            print(f"   → Progress: {(i/total)*100:.1f}%")

        y = span["bbox"][1]
        baselines.append(y)

    baseline_std = np.std(baselines)

    # Z-score anomaly detection
    mean = np.mean(baselines)
    std = np.std(baselines)

    anomaly_count = 0
    for y in baselines:
        if std > 0:
            z = (y - mean) / std
            if abs(z) > 2.5:
                anomaly_count += 1

    # 🔥 NEW FEATURES
    overlap_count = compute_overlap_count(spans)
    spacing_variance = compute_spacing_variance(baselines)
    word_count = len(spans)
    max_local_overlap = compute_max_local_overlap(spans)

    print(f"   ✔ Baseline std: {baseline_std:.2f}")
    print(f"   ✔ Baseline anomalies: {anomaly_count}")
    print(f"   ✔ Overlap count: {overlap_count}")
    print(f"   ✔ Max local overlap: {max_local_overlap}")
    print(f"   ✔ Spacing variance: {spacing_variance:.2f}")
    print(f"   ✔ Word count: {word_count}\n")

    return {
        "baseline_std": float(baseline_std),
        "baseline_anomaly_count": anomaly_count,
        "overlap_count": overlap_count,
        "max_local_overlap": max_local_overlap,
        "spacing_variance": spacing_variance,
        "word_count": word_count
    }