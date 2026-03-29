from PIL import Image, ImageChops
import numpy as np

def compute_ela(image_path, quality=90):
    print(f"      → Running ELA on {image_path}")

    original = Image.open(image_path).convert("RGB")

    temp_path = "temp_ela.jpg"
    original.save(temp_path, "JPEG", quality=quality)

    compressed = Image.open(temp_path)
    ela_image = ImageChops.difference(original, compressed)

    ela_array = np.array(ela_image)

    mean = np.mean(ela_array)
    var = np.var(ela_array)
    high_pixels = np.sum(ela_array > 50)

    return {
        "ela_mean": float(mean),
        "ela_variance": float(var),
        "ela_high_pixels": int(high_pixels)
    }