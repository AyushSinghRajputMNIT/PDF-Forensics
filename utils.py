import numpy as np

def safe_mean(arr):
    return float(np.mean(arr)) if len(arr) > 0 else 0.0

def safe_std(arr):
    return float(np.std(arr)) if len(arr) > 0 else 0.0