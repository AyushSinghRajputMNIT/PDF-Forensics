#!/usr/bin/env python3
"""
Dependencies:
  pip install pikepdf pymupdf

Usage:
  python extract_pdf_features.py input.pdf -o features.json

"""

from __future__ import annotations
import argparse
import json
import logging
import math
import os
import re
import statistics
import sys
from collections import defaultdict, Counter
from datetime import datetime

try:
    import pikepdf
except Exception:
    pikepdf = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("pdf-features")


# ---------- Raw-byte heuristics ----------

STREAM_RE = re.compile(rb"<<(?:(?:(?!>>).)*)/Length\s+(\d+)(?:(?:(?!>>).)*)>>\s*stream\r?\n", re.S)
OBJ_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj")
STARTXREF_RE = re.compile(rb"startxref\s+(\d+)", re.I)
XREF_LITERAL_RE = re.compile(rb"\nxref\s")
TRAILER_RE = re.compile(rb"trailer\b")


def read_file_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def analyze_xrefs(raw: bytes) -> dict:
    """Find occurrences of startxref, xref literal, and trailer as simple features."""
    starts = [int(m.group(1)) for m in STARTXREF_RE.finditer(raw)]
    num_startxref = len(starts)
    has_xref_literal = bool(XREF_LITERAL_RE.search(raw))
    trailer_count = len(TRAILER_RE.findall(raw))

    # offsets variance
    offsets_var = None
    if len(starts) >= 2:
        offsets_var = statistics.pstdev(starts)
    elif len(starts) == 1:
        offsets_var = 0.0

    return {
        "num_startxref": num_startxref,
        "startxref_offsets_sample": starts[:10],
        "startxref_offsets_variance": offsets_var,
        "has_xref_literal": has_xref_literal,
        "trailer_count": trailer_count,
    }


def analyze_objects(raw: bytes) -> dict:
    """Count objects and detect multiple revisions (same object id with multiple generation numbers).
    This is a heuristic based on regex matching of '<objnum> <gennum> obj'."""
    objs = OBJ_RE.findall(raw)
    obj_map = defaultdict(set)
    for on, gn in objs:
        obj_map[int(on)].add(int(gn))

    num_objects = len(obj_map)
    revisions = {k: sorted(list(v)) for k, v in obj_map.items()}
    objects_with_multiple_revisions = sum(1 for v in revisions.values() if len(v) > 1)
    max_revision_count = max((len(v) for v in revisions.values()), default=0)

    return {
        "num_objects_detected": num_objects,
        "objects_with_multiple_revisions": objects_with_multiple_revisions,
        "max_revision_count": max_revision_count,
        "revisions_sample": {k: revisions[k] for i, k in enumerate(list(revisions.keys())[:20])},
    }


def analyze_streams(raw: bytes) -> dict:
    """Detect stream sections based on pattern: '<< ... /Length N ... >>\nstream' and measure sizes."""
    stream_infos = []
    for m in STREAM_RE.finditer(raw):
        length_decl = int(m.group(1))
        start = m.end()
        # find endstream after start
        end_match = re.search(rb"\r?\nendstream", raw[start:start + length_decl + 2000])
        if end_match:
            # endstream found within expected window
            # compute actual stream byte length (until endstream)
            actual_len = end_match.start()
        else:
            # fallback: search for first occurrence of b'endstream' after start
            g = re.search(rb"endstream", raw[start:])
            actual_len = g.start() if g else None

        stream_infos.append({
            "decl_length": length_decl,
            "actual_length_found": actual_len,
        })

    lengths = [s["actual_length_found"] for s in stream_infos if s["actual_length_found"] is not None]
    declared = [s["decl_length"] for s in stream_infos]

    avg_actual = statistics.mean(lengths) if lengths else 0
    avg_declared = statistics.mean(declared) if declared else 0
    mismatch_count = sum(1 for s in stream_infos if s["actual_length_found"] is None or abs((s["actual_length_found"] or 0) - s["decl_length"]) > max(16, 0.1 * s["decl_length"]))

    return {
        "stream_count_detected": len(stream_infos),
        "avg_declared_stream_length": avg_declared,
        "avg_actual_stream_length": avg_actual,
        "stream_length_mismatch_count": mismatch_count,
    }


# ---------- Library-based metadata & pages & images ----------


def extract_metadata_with_pikepdf(path: str) -> dict:
    if pikepdf is None:
        logger.warning("pikepdf not installed; skipping metadata extraction via pikepdf")
        return {"pikepdf_available": False}

    try:
        pdf = pikepdf.Pdf.open(path)
    except Exception as e:
        logger.exception("pikepdf failed to open PDF: %s", e)
        return {"pikepdf_available": True, "error": str(e)}

    out = {"pikepdf_available": True}
    # docinfo (Info dictionary)
    try:
        info = {}
        for k, v in pdf.docinfo.items():
            # keys in pikepdf appear like '/Title' etc.
            try:
                info[str(k)] = str(v)
            except Exception:
                info[str(k)] = repr(v)
        out["info_dict"] = info
    except Exception:
        out["info_dict_error"] = "unable to read docinfo"

    # xmp metadata
    try:
        xm = pdf.open_metadata()
        xmp_dict = {k: str(v) for k, v in xm.items()}
        out["xmp"] = xmp_dict
    except Exception:
        out["xmp_error"] = "unable to read xmp"

    # page count
    try:
        out["page_count"] = len(pdf.pages)
    except Exception:
        out["page_count_error"] = "unable to count pages"

    # producer/creator heuristic
    try:
        creator = pdf.docinfo.get("/Creator") if "/Creator" in pdf.docinfo else pdf.docinfo.get("Creator")
        producer = pdf.docinfo.get("/Producer") if "/Producer" in pdf.docinfo else pdf.docinfo.get("Producer")
        out["creator"] = str(creator) if creator else None
        out["producer"] = str(producer) if producer else None
    except Exception:
        pass

    # creation / mod time gap (if present)
    def parse_pdf_date(s: str):
        # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
        try:
            if s.startswith("D:"):
                s2 = s[2:]
            else:
                s2 = s
            year = int(s2[0:4])
            month = int(s2[4:6]) if len(s2) >= 6 else 1
            day = int(s2[6:8]) if len(s2) >= 8 else 1
            hour = int(s2[8:10]) if len(s2) >= 10 else 0
            minute = int(s2[10:12]) if len(s2) >= 12 else 0
            second = int(s2[12:14]) if len(s2) >= 14 else 0
            return datetime(year, month, day, hour, minute, second)
        except Exception:
            return None

    try:
        creation = pdf.docinfo.get("/CreationDate") or pdf.docinfo.get("CreationDate")
        mod = pdf.docinfo.get("/ModDate") or pdf.docinfo.get("ModDate")
        cdt = parse_pdf_date(str(creation)) if creation else None
        mdt = parse_pdf_date(str(mod)) if mod else None
        if cdt and mdt:
            out["creation_modification_time_gap_seconds"] = (mdt - cdt).total_seconds()
            out["creation_date"] = cdt.isoformat()
            out["modification_date"] = mdt.isoformat()
        else:
            out["creation_modification_time_gap_seconds"] = None
    except Exception:
        out["creation_modification_time_gap_error"] = True

    return out


def extract_images_with_pymupdf(path: str) -> dict:
    if fitz is None:
        logger.warning("PyMuPDF (fitz) not installed; skipping image extraction")
        return {"pymupdf_available": False}

    try:
        doc = fitz.open(path)
    except Exception as e:
        logger.exception("PyMuPDF failed to open PDF: %s", e)
        return {"pymupdf_available": True, "error": str(e)}

    images = []
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        try:
            imglist = page.get_images(full=True)
        except Exception:
            imglist = []
        for img in imglist:
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                ext = base_image.get("ext")
                width = base_image.get("width")
                height = base_image.get("height")
                size = len(base_image.get("image")) if base_image.get("image") else None
                images.append({
                    "page_index": page_index,
                    "xref": xref,
                    "ext": ext,
                    "width": width,
                    "height": height,
                    "size_bytes": size,
                })
            except Exception:
                continue

    out = {"pymupdf_available": True, "images": images, "image_count": len(images)}
    if images:
        widths = [i["width"] for i in images if i.get("width")]
        heights = [i["height"] for i in images if i.get("height")]
        out["avg_image_width"] = statistics.mean(widths) if widths else None
        out["avg_image_height"] = statistics.mean(heights) if heights else None
        out["image_ext_counts"] = dict(Counter([i.get("ext") for i in images if i.get("ext")]))
    return out


# ---------- Assemble features ----------


def assemble_features(path: str) -> dict:
    logger.info("Reading raw bytes from %s", path)
    raw = read_file_bytes(path)

    logger.info("Analyzing xrefs (raw heuristics)")
    xref_info = analyze_xrefs(raw)

    logger.info("Analyzing objects (raw heuristics)")
    obj_info = analyze_objects(raw)

    logger.info("Analyzing streams (raw heuristics)")
    stream_info = analyze_streams(raw)

    logger.info("Extracting metadata (pikepdf)")
    md = extract_metadata_with_pikepdf(path)

    logger.info("Extracting images (PyMuPDF)")
    imgs = extract_images_with_pymupdf(path)

    metadata_mismatch = False
    try:
        creator = md.get("creator") if md.get("pikepdf_available") else None
        producer = md.get("producer") if md.get("pikepdf_available") else None
        if creator and producer and creator != producer:
            metadata_mismatch = True
    except Exception:
        metadata_mismatch = False

    features = {
        "file_path": os.path.abspath(path),
        "file_size_bytes": len(raw),
        "xref": xref_info,
        "objects": obj_info,
        "streams": stream_info,
        "metadata": md,
        "images": imgs,
        "metadata_mismatch_creator_producer": metadata_mismatch,
    }

    try:
        features["num_startxref"] = xref_info.get("num_startxref")
        features["detected_stream_count"] = stream_info.get("stream_count_detected")
        features["num_objects_detected"] = obj_info.get("num_objects_detected")
        features["page_count"] = md.get("page_count") if md.get("pikepdf_available") else None
    except Exception:
        pass

    return features


# ---------- CLI ----------


def parse_args():
    p = argparse.ArgumentParser(description="Extract low-level PDF structural features")
    p.add_argument("pdf", help="Input PDF file path")
    p.add_argument("-o", "--output", default=None, help="Output JSON file (default: <pdf>.features.json)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return p.parse_args()


def main():
    args = parse_args()
    path = args.pdf
    if not os.path.isfile(path):
        logger.error("File not found: %s", path)
        sys.exit(2)

    features = assemble_features(path)

    outpath = args.output or (path + ".features.json")
    with open(outpath, "w", encoding="utf-8") as f:
        if args.pretty:
            json.dump(features, f, indent=2, ensure_ascii=False)
        else:
            json.dump(features, f, ensure_ascii=False)

    logger.info("Features written to %s", outpath)


if __name__ == "__main__":
    main()
