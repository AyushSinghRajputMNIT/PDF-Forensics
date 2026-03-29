import numpy as np

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

    print(f"   ✔ Baseline std: {baseline_std:.2f}")
    print(f"   ✔ Baseline anomalies: {anomaly_count}\n")

    return {
        "baseline_std": float(baseline_std),
        "baseline_anomaly_count": anomaly_count
    }