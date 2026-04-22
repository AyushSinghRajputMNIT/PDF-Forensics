from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import matplotlib.pyplot as plt
import numpy as np
import json
import io
import shutil
import uuid
import os

from predict import predict_pdf

# =========================
# FASTAPI SETUP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# CHART FUNCTIONS
# =========================

def create_bar_chart(rf, xgb):
    fig, ax = plt.subplots()

    ax.bar(["RF", "XGB"], [rf, xgb])
    ax.set_title("Model Comparison")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf


def create_doughnut(confidence):
    fig, ax = plt.subplots()

    ax.pie(
        [confidence, 1 - confidence],
        labels=["Confidence", "Remaining"],
        autopct="%1.1f%%"
    )

    ax.set_title("Confidence Score")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf


def create_radar_chart(tampering_types):
    labels = [t["type"] for t in tampering_types]
    values = [t["confidence"] for t in tampering_types]

    N = len(labels)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()

    values += values[:1]
    angles += angles[:1]
    labels += labels[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels[:-1])

    ax.set_title("Tampering Type Analysis")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    return buf

# =========================
# PDF STYLING
# =========================

def section_break():
    return HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#e5e7eb"),
        spaceBefore=10,
        spaceAfter=10
    )

# =========================
# PDF GENERATOR
# =========================

def generate_pdf_report(data):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="ReportTitle",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=10,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="BodyTextCustom",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1f2937")
    ))

    styles.add(ParagraphStyle(
        name="CodeBlock",
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#111827")
    ))

    content = []

    # =========================
    # TITLE
    # =========================
    content.append(Paragraph("PDF Forensic Report", styles["ReportTitle"]))
    content.append(Spacer(1, 10))

    # =========================
    # BASIC INFO
    # =========================
    content.append(Paragraph(f"File: {data['pdf']}", styles["BodyTextCustom"]))
    content.append(Paragraph(f"Verdict: {data['forensic_verdict']}", styles["BodyTextCustom"]))
    content.append(Paragraph(f"Risk Level: {data['risk_level']}", styles["BodyTextCustom"]))
    content.append(Paragraph(f"Confidence: {data['confidence']}", styles["BodyTextCustom"]))
    content.append(section_break())

    # =========================
    # CHARTS
    # =========================
    bar_chart = create_bar_chart(data["rf_probability"], data["xgb_probability"])
    doughnut_chart = create_doughnut(data["confidence"])
    radar_chart = create_radar_chart(data["tampering_types"])

    content.append(Paragraph("Visual Forensic Analysis", styles["SectionHeader"]))

    content.append(Image(radar_chart, width=400, height=250))
    content.append(Spacer(1, 10))

    content.append(Image(bar_chart, width=400, height=180))
    content.append(Spacer(1, 10))

    content.append(Image(doughnut_chart, width=300, height=180))

    content.append(section_break())

    # =========================
    # SUMMARY
    # =========================
    content.append(Paragraph("Case Summary", styles["SectionHeader"]))
    content.append(Paragraph(data["case_summary"], styles["BodyTextCustom"]))
    content.append(section_break())

    # =========================
    # TAMPERING TYPES
    # =========================
    content.append(Paragraph("Tampering Evidence", styles["SectionHeader"]))

    for t in data["tampering_types"]:
        content.append(Paragraph(
            f"• {t['type']} — confidence {t['confidence']}",
            styles["BodyTextCustom"]
        ))

    content.append(section_break())

    # =========================
    # EXPLANATION
    # =========================
    content.append(Paragraph("Forensic Explanation", styles["SectionHeader"]))

    for e in data["explanation"]:
        content.append(Paragraph(f"• {e}", styles["BodyTextCustom"]))

    content.append(section_break())

    # =========================
    # RAW OUTPUT
    # =========================
    content.append(Paragraph("Raw Output (JSON)", styles["SectionHeader"]))

    raw_json = json.dumps(data, indent=2)

    for line in raw_json.split("\n"):
        content.append(Paragraph(line, styles["CodeBlock"]))

    # Build PDF
    doc.build(content)
    buffer.seek(0)

    return buffer

# =========================
# API ENDPOINTS
# =========================

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    file_id = uuid.uuid4().hex[:12]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = predict_pdf(file_path)
        result["pdf"] = file.filename
        return result

    finally:
        try:
            os.remove(file_path)
        except:
            pass


@app.post("/export-report")
async def export_report(payload: dict):

    pdf_buffer = generate_pdf_report(payload)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=forensic_report_{payload.get('pdf','report')}.pdf"
        }
    )