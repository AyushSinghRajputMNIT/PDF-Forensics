import os
import random
import csv
import re
import glob
import datetime
import pikepdf
import fitz  # PyMuPDF

GENUINE_DIR = "dataset/genuine"
TAMPERED_DIR = "dataset/tampered"
LABEL_FILE = "dataset/labels.csv"

os.makedirs(TAMPERED_DIR, exist_ok=True)

labels = []


# -------------------------------
# 1. Metadata Tampering
# -------------------------------
def tamper_metadata(input_path, output_path):
    try:
        pdf = pikepdf.open(input_path)

        pdf.docinfo["/Author"] = "User_" + str(random.randint(100, 999))

        # ✅ Always save to different file
        if input_path == output_path:
            output_path = output_path.replace(".pdf", "_meta_fix.pdf")

        pdf.save(output_path)
        return True

    except Exception as e:
        print(f"[METADATA ERROR] {e}")
        return False


# -------------------------------
# 2. Resave Tampering
# -------------------------------
def tamper_resave(input_path, output_path):
    try:
        pdf = pikepdf.open(input_path)

        now = datetime.datetime.now().strftime("D:%Y%m%d%H%M%S")
        pdf.docinfo["/ModDate"] = now

        # ✅ Avoid overwrite
        if input_path == output_path:
            output_path = output_path.replace(".pdf", "_resave_fix.pdf")

        pdf.save(output_path)
        return True

    except Exception as e:
        print(f"[RESAVE ERROR] {e}")
        return False


# -------------------------------
# 3. Subtle Text Change
# -------------------------------
def subtle_text_change(text):
    def modify_number(match):
        try:
            num = int(match.group())
            return str(num + random.randint(-5, 20))
        except:
            return match.group()

    text = re.sub(r"\b\d+\b", modify_number, text)

    replacements = {
        "Total": "SubTotal",
        "Amount": "Amt",
        "Date": "Dt",
        "Number": "No.",
        "Invoice": "Bill",
    }

    for k, v in replacements.items():
        if random.random() < 0.3:
            text = text.replace(k, v)

    return text


# -------------------------------
# 4. Text Tampering (REALISTIC)
# -------------------------------
def tamper_text(input_path, output_path, max_pages=3):
    try:
        doc = fitz.open(input_path)
        pages_to_modify = min(max_pages, len(doc))

        for i in range(pages_to_modify):
            page = doc[i]

            if random.random() < 0.7:
                words = page.get_text("words")
                if not words:
                    continue

                selected_words = random.sample(words, min(5, len(words)))

                for w in selected_words:
                    x0, y0, x1, y1, word, *_ = w

                    new_word = subtle_text_change(word)

                    rect = fitz.Rect(x0, y0, x1, y1)

                    # Mask original word
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

                    # Slight misalignment
                    dx = random.uniform(-1.5, 1.5)
                    dy = random.uniform(-1.5, 1.5)

                    font_size = max(6, min(12, (y1 - y0) * random.uniform(0.8, 1.2)))

                    # Replace IN SAME LOCATION (not above)
                    page.insert_text(
                        (x0 + dx, y1 + dy),
                        new_word,
                        fontsize=font_size
                    )

        doc.save(output_path)
        return True

    except Exception as e:
        print(f"[TEXT ERROR] {e}")
        return False


# -------------------------------
# 5. Overlay Tampering
# -------------------------------
def overlay_tamper(input_path, output_path, max_pages=3):
    try:
        doc = fitz.open(input_path)
        pages_to_modify = min(max_pages, len(doc))

        for i in range(pages_to_modify):
            page = doc[i]

            if random.random() < 0.5:
                for _ in range(random.randint(1, 2)):
                    x = random.randint(50, 400)
                    y = random.randint(50, 700)

                    text = random.choice(["Verified", "Checked", "OK", "Done"])

                    page.insert_text(
                        (x, y),
                        text,
                        fontsize=random.randint(6, 10)
                    )

        doc.save(output_path)
        return True

    except Exception as e:
        print(f"[OVERLAY ERROR] {e}")
        return False


# -------------------------------
# MAIN PIPELINE
# -------------------------------
def process():
    FITZ_TYPES = {"text", "overlay"}
    PIKEPDF_TYPES = {"metadata", "resave"}

    files = [f for f in os.listdir(GENUINE_DIR) if f.endswith(".pdf")]

    for file in files:
        input_path = os.path.join(GENUINE_DIR, file)

        # Genuine entry
        labels.append([file, 0, "none"])

        # -------------------------------
        # Controlled tampering selection
        # -------------------------------
        tamper_types = []

        if random.random() < 0.6:
            tamper_types.append("text")

        if random.random() < 0.5:
            tamper_types.append("overlay")

        if random.random() < 0.6:
            tamper_types.append("metadata")

        if random.random() < 0.6:
            tamper_types.append("resave")

        # Ensure at least one tamper
        if not tamper_types:
            tamper_types.append(random.choice(["text", "metadata"]))

        # Ensure structural + content mix sometimes
        if "text" in tamper_types and random.random() < 0.5:
            tamper_types.append("metadata")

        # Order: FITZ first → PIKEPDF later
        tamper_types = (
            [t for t in tamper_types if t in FITZ_TYPES] +
            [t for t in tamper_types if t in PIKEPDF_TYPES]
        )

        current_input = input_path

        # -------------------------------
        # Apply sequential tampering
        # -------------------------------
        for t in tamper_types:
            temp_output = os.path.join(
                TAMPERED_DIR,
                f"temp_{t}_{random.randint(10000,99999)}_{file}"
            )

            if t == "text":
                success = tamper_text(current_input, temp_output)

            elif t == "overlay":
                success = overlay_tamper(current_input, temp_output)

            elif t == "metadata":
                success = tamper_metadata(current_input, temp_output)

            elif t == "resave":
                success = tamper_resave(current_input, temp_output)

            else:
                success = False

            if success:
                current_input = temp_output

        # -------------------------------
        # Finatemp_outputl output
        # -------------------------------
        final_output = os.path.join(
            TAMPERED_DIR,
            file.replace(".pdf", "_tampered.pdf")
        )

        if os.path.exists(current_input) and current_input != input_path:
            os.rename(current_input, final_output)
            labels.append([
                os.path.basename(final_output),
                1,
                "+".join(tamper_types)
            ])

        print(f"[DONE] {file} → {tamper_types}")

    # Cleanup temp files
    for f in glob.glob(os.path.join(TAMPERED_DIR, "temp_*")):
        try:
            os.remove(f)
        except:
            pass

    # Save labels
    with open(LABEL_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pdf_name", "label", "tamper_type"])
        writer.writerows(labels)

    print("\n✅ Tampering complete. Clean & realistic dataset ready.")


if __name__ == "__main__":
    process()