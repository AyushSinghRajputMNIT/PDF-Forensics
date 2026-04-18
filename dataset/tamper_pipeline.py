import os
import random
import csv
import glob
import datetime
import pikepdf
import fitz
import numpy as np
import cv2
import io
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

# -------------------------------
# PATHS
# -------------------------------
GENUINE_DIR = "dataset/genuine"
TAMPERED_DIR = "dataset/tampered"
TAMPER_IMG_DIR = "dataset/tamper_images"
LABEL_FILE = "dataset/labels.csv"

MIN_SIZE = 20

os.makedirs(TAMPERED_DIR, exist_ok=True)
labels = []

# -------------------------------
# SAFE UTILS
# -------------------------------
def safe_randint(low, high):
    return low if high <= low else random.randint(low, high)

def safe_text():
    return random.choice(["Authorized", "Signed", "Approved"])

def load_image_any_format(path):
    try:
        img = Image.open(path)
        return img.convert("RGBA")
    except:
        return None


def get_all_tamper_images():
    imgs = []
    for root, _, files in os.walk(TAMPER_IMG_DIR):
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                full = os.path.join(root, f)
                img = load_image_any_format(full)
                if img:
                    imgs.append((full, img))
    return imgs


TAMPER_IMAGES = get_all_tamper_images()


# -------------------------------
# IMAGE CLASSIFICATION
# -------------------------------
def classify_image(img):
    arr = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    h, w = gray.shape
    aspect = w / (h + 1e-6)

    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.mean(edges)

    if edge_density > 20 and aspect > 1.5:
        return "signature"
    if edge_density > 10:
        return "stamp"
    return "logo"


def pick_tamper_image():
    if not TAMPER_IMAGES:
        return None
    path, img = random.choice(TAMPER_IMAGES)
    return path, img, classify_image(img)


# =========================================================
# STRUCTURAL TAMPERING
# =========================================================
def tamper_metadata(input_path, output_path):
    try:
        pdf = pikepdf.open(input_path)
        pdf.docinfo["/Author"] = f"User_{random.randint(100,999)}"
        pdf.save(output_path)
        return True
    except Exception as e:
        print(f"[METADATA ERROR] {e}")
        return False


def tamper_resave(input_path, output_path):
    try:
        pdf = pikepdf.open(input_path)
        now = datetime.datetime.now().strftime("D:%Y%m%d%H%M%S")
        pdf.docinfo["/ModDate"] = now
        pdf.save(output_path)
        return True
    except Exception as e:
        print(f"[RESAVE ERROR] {e}")
        return False


# =========================================================
# TEXT TAMPERING
# =========================================================
def tamper_text(input_path, output_path, max_pages=3):
    try:
        doc = fitz.open(input_path)

        for i in range(min(max_pages, len(doc))):
            page = doc[i]
            words = page.get_text("words")

            if not words:
                continue

            for w in random.sample(words, min(5, len(words))):
                x0, y0, x1, y1, word, *_ = w
                rect = fitz.Rect(x0, y0, x1, y1)

                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                page.insert_text((x0, y1), word, fontsize=8)

        doc.save(output_path)
        return True

    except Exception as e:
        print(f"[TEXT ERROR] {e}")
        return False


# =========================================================
# OVERLAY TAMPERING
# =========================================================
def overlay_tamper(input_path, output_path, max_pages=3):
    try:
        doc = fitz.open(input_path)

        for i in range(min(max_pages, len(doc))):
            page = doc[i]

            if random.random() < 0.5:
                x = safe_randint(50, int(page.rect.width) - 50)
                y = safe_randint(50, int(page.rect.height) - 50)

                page.insert_text((x, y), safe_text(), fontsize=10)

        doc.save(output_path)
        return True

    except Exception as e:
        print(f"[OVERLAY ERROR] {e}")
        return False


# =========================================================
# 1. EMBEDDED IMAGE REPLACEMENT (SIGNATURE / STAMP / LOGO ONLY)
# =========================================================
def tamper_embedded_images(input_path, output_path):
    try:
        doc = fitz.open(input_path)
        tampered = False

        for page in doc:
            images = page.get_images(full=True)
            if not images:
                continue

            used_rects = []

            for img in images:
                if random.random() > 0.6:
                    continue

                xref = img[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue

                rect = rects[0]

                if any(rect.intersects(r) for r in used_rects):
                    continue
                used_rects.append(rect)

                img_data = pick_tamper_image()
                if not img_data:
                    continue

                _, pil_img, img_type = img_data

                w, h = int(rect.width), int(rect.height)
                if w < MIN_SIZE or h < MIN_SIZE:
                    continue

                pil_img = pil_img.resize((w, h))

                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")

                page.insert_image(rect, stream=buf.getvalue())
                tampered = True

        if tampered:
            doc.save(output_path)
            return True

        return False

    except Exception as e:
        print(f"[EMBEDDED IMAGE ERROR] {e}")
        return False


# =========================================================
# 2. INTERNAL IMAGE TAMPERING (PIXEL-LEVEL ATTACKS)
# =========================================================
def tamper_internal_image_noise(input_path, output_path):
    """
    Applies:
    - copy-move
    - patch edit
    - blending
    INSIDE existing embedded images
    """
    try:
        doc = fitz.open(input_path)
        tampered = False

        for page in doc:
            images = page.get_images(full=True)
            if not images:
                continue

            for img in images:
                xref = img[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue

                rect = rects[0]

                pix = page.get_pixmap(clip=rect)

                img_np = np.frombuffer(pix.samples, dtype=np.uint8)

                img_np = img_np.reshape(pix.height, pix.width, pix.n).copy()

                img_np = np.ascontiguousarray(img_np)
                img_np.flags.writeable = True

                h, w = img_np.shape[:2]

                if w < MIN_SIZE or h < MIN_SIZE:
                    continue

                mode = random.choice(["copy_move", "patch_edit", "blend"])

                # COPY-MOVE
                if mode == "copy_move":
                    pw, ph = w // 3, h // 3
                    if pw <= 0 or ph <= 0:
                        continue

                    x1 = random.randint(0, w - pw)
                    y1 = random.randint(0, h - ph)

                    patch = img_np[y1:y1+ph, x1:x1+pw].copy()

                    x2 = random.randint(0, w - pw)
                    y2 = random.randint(0, h - ph)

                    img_np[y2:y2+ph, x2:x2+pw] = patch

                # PATCH EDIT
                elif mode == "patch_edit":
                    rw, rh = w // 4, h // 4
                    if w - rw <= 0 or h - rh <= 0:
                        continue

                    x = random.randint(0, w - rw)
                    y = random.randint(0, h - rh)

                    noise = np.random.randint(0, 255,(rh, rw, img_np.shape[2]),dtype=np.uint8).copy()

                    img_np[y:y+rh, x:x+rw] = noise

                # BLEND
                elif mode == "blend":
                    overlay = img_np.copy()
                    bw, bh = min(30, w), min(30, h)

                    if w - bw <= 0 or h - bh <= 0:
                        continue

                    x = random.randint(0, w - bw)
                    y = random.randint(0, h - bh)

                    color = random.choice([
                        (255, 0, 0),
                        (0, 255, 0),
                        (0, 0, 255)
                    ])

                    cv2.rectangle(overlay, (x, y), (x+bw, y+bh), color, -1)

                    img_np = cv2.addWeighted(overlay, 0.5, img_np, 0.5, 0)

                pil_out = Image.fromarray(img_np)
                buf = io.BytesIO()
                pil_out.save(buf, format="PNG")

                page.insert_image(rect, stream=buf.getvalue())
                tampered = True

        if tampered:
            doc.save(output_path)
            return True

        return False

    except Exception as e:
        print(f"[INTERNAL IMAGE ERROR] {e}")
        return False


# =========================================================
# MAIN PIPELINE
# =========================================================
def process():
    files = [f for f in os.listdir(GENUINE_DIR) if f.endswith(".pdf")]

    for file in files:
        input_path = os.path.join(GENUINE_DIR, file)

        try:
            fitz.open(input_path).close()
        except:
            print(f"[CORRUPT] {file}")
            continue

        labels.append([file, 0, "none"])

        tamper_types = []

        if random.random() < 0.6:
            tamper_types.append("text")
        if random.random() < 0.5:
            tamper_types.append("overlay")
        if random.random() < 0.5:
            tamper_types.append("embedded_image")
        if random.random() < 0.5:
            tamper_types.append("internal_image")
        if random.random() < 0.6:
            tamper_types.append("metadata")
        if random.random() < 0.6:
            tamper_types.append("resave")

        # occasional MIXED ATTACKS
        if random.random() < 0.3:
            tamper_types.append("embedded_image")
            tamper_types.append("internal_image")

        if not tamper_types:
            tamper_types.append(random.choice([
                "text",
                "overlay",
                "metadata",
                "resave"
            ]))

        current = input_path
        applied = []

        for t in tamper_types:
            out = os.path.join(
                TAMPERED_DIR,
                f"temp_{t}_{random.randint(10000,99999)}_{file}"
            )

            if t == "text":
                ok = tamper_text(current, out)
            elif t == "overlay":
                ok = overlay_tamper(current, out)
            elif t == "embedded_image":
                ok = tamper_embedded_images(current, out)
            elif t == "internal_image":
                ok = tamper_internal_image_noise(current, out)
            elif t == "metadata":
                ok = tamper_metadata(current, out)
            elif t == "resave":
                ok = tamper_resave(current, out)
            else:
                ok = False

            if ok:
                current = out
                applied.append(t)

        if not applied:
            print(f"[FALLBACK] {file} → applying safe text tamper")

            out = os.path.join(TAMPERED_DIR, f"fallback_text_{random.randint(10000,99999)}_{file}")

            tamper_text(input_path, out)

            current = out
            applied = ["text_fallback"]

        final = os.path.join(TAMPERED_DIR, file.replace(".pdf", "_tampered.pdf"))
        os.rename(current, final)

        labels.append([os.path.basename(final), 1, "+".join(applied)])
        print(f"[DONE] {file} → {applied}")

    for f in glob.glob(os.path.join(TAMPERED_DIR, "temp_*")):
        try:
            os.remove(f)
        except:
            pass

    with open(LABEL_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdf_name", "label", "tamper_type"])
        w.writerows(labels)

    print("\n✅ Pipeline complete")


if __name__ == "__main__":
    process()