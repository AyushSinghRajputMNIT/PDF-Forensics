import numpy as np
from collections import Counter
import math

def entropy(counter):
    total = sum(counter.values())
    return -sum((v/total) * math.log(v/total) for v in counter.values() if v > 0)

def sliding_window_entropy(spans, window_size=5):
    print("\n[4/4] Running font anomaly detection (sliding window)...")

    fonts = [s["font"] for s in spans]

    entropies = []
    anomaly_count = 0

    for i in range(len(fonts) - window_size + 1):
        window = fonts[i:i+window_size]
        freq = Counter(window)

        e = entropy(freq)
        entropies.append(e)

    if not entropies:
        return {"font_entropy": 0, "font_count": 0, "font_anomaly": 0}

    mean = np.mean(entropies)
    std = np.std(entropies)

    for e in entropies:
        if std > 0 and e > mean + 2 * std:
            anomaly_count += 1

    print(f"   ✔ Font entropy mean: {mean:.3f}")
    print(f"   ✔ Font anomaly windows: {anomaly_count}\n")

    return {
        "font_entropy": float(mean),
        "font_count": len(set(fonts)),
        "font_anomaly": anomaly_count
    }