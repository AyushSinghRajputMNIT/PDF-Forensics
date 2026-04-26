from __future__ import annotations
import argparse
import json
import math
import os
import statistics
from typing import Any, Dict


def safe_get(d: Dict, *keys, default=None):
    v = d
    try:
        for k in keys:
            v = v[k]
        return v
    except Exception:
        return default


class StructuralAnalyzer:
    def __init__(self, features: Dict[str, Any]):
        self.f = features
        self.suspicion = 0.0
        self.explanations = []

    def analyze(self):
        self.suspicion = 0.0
        self.explanations.clear()

        self._analyze_xref()
        self._analyze_objects()
        self._analyze_streams()
        self._analyze_metadata()
        self._analyze_images()
        self._analyze_structure_irregularities()

        # Normalize into 0-100 score
        max_score = 20.0
        score = (self.suspicion / max_score) * 100.0
        score = max(0.0, min(100.0, score))

        category = self._categorize(score)

        return {
            "structural_suspicion_score": score,
            "suspicion_raw": self.suspicion,
            "max_raw_score": max_score,
            "category": category,
            "explanations": self.explanations,
        }

    def _add(self, amount: float, reason: str):
        self.suspicion += amount
        self.explanations.append({"add": amount, "reason": reason})

    def _analyze_xref(self):
        xref = self.f.get("xref", {})
        num_startxref = xref.get("num_startxref", 0) or 0
        has_xref_literal = bool(xref.get("has_xref_literal"))
        offsets_var = xref.get("startxref_offsets_variance")

        if num_startxref <= 1:
            pass
        elif num_startxref == 2:
            self._add(1.0, "Two startxref entries (one incremental update)")
        elif num_startxref == 3:
            self._add(2.0, "Three startxref entries (multiple edits)")
        else:
            self._add(3.0, f"{num_startxref} startxref entries (very likely edited multiple times)")

        if has_xref_literal and num_startxref > 1:
            self._add(1.5, "Contains literal 'xref' plus incremental updates (mixed xref styles)")

        if offsets_var is not None:
            try:
                if offsets_var < 50 and num_startxref > 1:
                    self._add(1.0, f"startxref offsets variance very small ({offsets_var}); suspicious manual patching")
                elif offsets_var is not None and offsets_var > 100000:
                    # large variance uncommon; penalize lightly
                    self._add(0.5, f"startxref offsets variance large ({offsets_var}); uncommon structure")
            except Exception:
                pass

    def _analyze_objects(self):
        objs = self.f.get("objects", {})
        revs = objs.get("objects_with_multiple_revisions", 0) or 0
        max_rev = objs.get("max_revision_count", 0) or 0
        num_objects = objs.get("num_objects_detected", None)

        if revs > 20:
            self._add(4.0, f"Many objects with multiple revisions ({revs}); strong editing signal")
        elif revs > 10:
            self._add(3.0, f"Several objects with multiple revisions ({revs}); suspicious")
        elif revs > 5:
            self._add(1.0, f"Some objects with multiple revisions ({revs})")

        if max_rev >= 5:
            self._add(4.0, f"Max object generation count is high ({max_rev})")
        elif max_rev >= 3:
            self._add(2.0, f"Max object generation count moderately high ({max_rev})")

        # small file with very few objects but many streams checked in other function
        if num_objects is not None and num_objects < 10:
            self._add(0.5, f"Very few objects detected ({num_objects}); unusual structure for complex documents")

    def _analyze_streams(self):
        streams = self.f.get("streams", {})
        mismatch = streams.get("stream_length_mismatch_count", 0) or 0
        avg_decl = streams.get("avg_declared_stream_length", 0) or 0
        avg_act = streams.get("avg_actual_stream_length", 0) or 0
        stream_count = streams.get("stream_count_detected", 0) or 0

        if mismatch >= 5:
            self._add(5.0, f"Many stream length mismatches ({mismatch}); strong indicator of manual edits")
        elif mismatch >= 2:
            self._add(2.0, f"Stream length mismatches found ({mismatch})")

        try:
            if avg_decl > 0 and avg_act > 0:
                rel = abs(avg_decl - avg_act) / max(avg_decl, 1)
                if rel > 0.30:
                    self._add(3.0, f"Average declared vs actual stream length mismatch {rel*100:.1f}%")
                elif rel > 0.10:
                    self._add(1.0, f"Small average declared/actual stream length mismatch {rel*100:.1f}%")
        except Exception:
            pass

        # if many streams but few objects (checked here)
        num_objects = safe_get(self.f, "objects", "num_objects_detected", default=None)
        if num_objects is not None and num_objects < 20 and stream_count > 20:
            self._add(2.5, f"Low object count ({num_objects}) with many streams ({stream_count}); suspicious object injection")

    def _analyze_metadata(self):
        md = self.f.get("metadata", {})
        mismatch_flag = bool(self.f.get("metadata_mismatch_creator_producer", False))
        creation_gap = md.get("creation_modification_time_gap_seconds", None)
        creator = md.get("creator")
        producer = md.get("producer")
        num_startxref = safe_get(self.f, "xref", "num_startxref", default=0) or 0

        if mismatch_flag and num_startxref <= 1:
            self._add(2.0, "Creator/Producer mismatch with only a single startxref (metadata conflict)")

        if creation_gap is not None:
            try:
                if creation_gap < 0:
                    self._add(4.0, f"Modification time is earlier than creation time (gap={creation_gap} sec); impossible without tampering")
                elif creation_gap == 0:
                    # zero gap sometimes normal; small penalty
                    self._add(0.25, "Creation and modification time identical (possible re-save)")
                elif creation_gap < 60:
                    # modified within a minute — could be benign, but note
                    self._add(0.5, f"Creation and modification very close ({creation_gap} sec)")
            except Exception:
                pass

        # odd producers
        if producer and isinstance(producer, str):
            lower = producer.lower()
            if "ghostscript" in lower or "libharu" in lower or "qpdf" in lower:
                # these can be benign; penalize slightly if other flags present
                self._add(0.3, f"Producer indicates non-standard tool: {producer}")

    def _analyze_images(self):
        imgs = self.f.get("images", {})
        img_count = imgs.get("image_count", 0) or 0
        if img_count == 0:
            return

        widths = [i.get("width") for i in imgs.get("images", []) if i.get("width")]
        heights = [i.get("height") for i in imgs.get("images", []) if i.get("height")]

        if widths and len(widths) > 1:
            try:
                w_var = statistics.pstdev(widths)
                h_var = statistics.pstdev(heights) if heights else 0
                if w_var > max(50, statistics.mean(widths) * 0.6):
                    self._add(1.5, f"High variance in image widths ({w_var}); possible image replacement")
                if h_var > max(50, statistics.mean(heights) * 0.6):
                    self._add(1.5, f"High variance in image heights ({h_var}); possible image replacement")
            except Exception:
                pass

    def _analyze_structure_irregularities(self):
        # orphan objects / reference graph detection isn't in extract features yet, but we can use heuristics
        objs = safe_get(self.f, "objects", "num_objects_detected", default=None)
        pages = safe_get(self.f, "metadata", "page_count", default=None)
        file_size = self.f.get("file_size_bytes", None)

        if objs is not None and pages is not None:
            # very rough heuristic: PDFs with many pages usually have many objects
            if pages > 50 and objs is not None and objs < pages * 2:
                self._add(0.7, f"Unusually low object count ({objs}) for many pages ({pages}); suspicious")

        if file_size is not None and file_size < 1024:
            self._add(1.0, "Tiny PDF file size (<1KB); suspicious / probably malformed")

    def _categorize(self, score: float) -> str:
        if score < 20:
            return "CLEAN/LOW_RISK"
        if score < 40:
            return "MINOR_ANOMALY"
        if score < 60:
            return "SUSPICIOUS"
        if score < 80:
            return "LIKELY_TAMPERED"
        return "VERY_LIKELY_TAMPERED"


def load_features(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_report(report: Dict[str, Any], outpath: str, pretty: bool = False):
    with open(outpath, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            json.dump(report, f, ensure_ascii=False)


def print_summary(report: Dict[str, Any]):
    score = report.get("structural_suspicion_score")
    cat = report.get("category")
    print("=== Structural Analysis Summary ===")
    print(f"Suspicion Score: {score:.1f}%  ({cat})")
    print("Top reasons:")
    for e in report.get("explanations", [])[:8]:
        qty = e.get("add")
        reason = e.get("reason")
        print(f"  +{qty:.2f} -> {reason}")
    print("===================================")


def parse_args():
    p = argparse.ArgumentParser(description="Analyze structural PDF features and produce forgery suspicion score")
    p.add_argument("features", help="Input features JSON file produced by extract_structural_features.py")
    p.add_argument("-o", "--output", default=None, help="Output JSON report (default: <features>.analysis.json)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print output JSON")
    return p.parse_args()


def main():
    args = parse_args()
    path = args.features
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        raise SystemExit(2)

    features = load_features(path)
    analyzer = StructuralAnalyzer(features)
    report = analyzer.analyze()

    report_out = {
        "analyzed_from": os.path.abspath(path),
        "analysis": report,
    }

    outpath = args.output or (path + ".analysis.json")
    write_report(report_out, outpath, pretty=args.pretty)
    print_summary(report["analysis"] if "analysis" in report else report)
    print(f"Report written to: {outpath}")


if __name__ == "__main__":
    main()
