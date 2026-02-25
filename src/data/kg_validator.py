#!/usr/bin/env python3
"""Validate candidate triples against reference KG."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .io_utils import load_json_records, save_json_records
except ImportError:  # pragma: no cover
    from io_utils import load_json_records, save_json_records


def load_reference_kg(path: str | Path) -> tuple[set[tuple[str, str, str]], dict[tuple[str, str], tuple[float, float]]]:
    rows = load_json_records(path)
    triples: set[tuple[str, str, str]] = set()
    dosage_ranges: dict[tuple[str, str], tuple[float, float]] = {}

    for row in rows:
        h = str(row.get("head", "")).strip()
        r = str(row.get("relation", "")).strip()
        t = str(row.get("tail", "")).strip()
        if h and r and t:
            triples.add((h, r, t))

        if r == "dosage_range_mg":
            m = re.match(r"(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)", t)
            if m:
                dosage_ranges[(h, "mg")] = (float(m.group(1)), float(m.group(2)))

    return triples, dosage_ranges


def parse_dose(value: str) -> tuple[float, str] | None:
    m = re.match(r"(\d+(?:\.\d+)?)\s*(mg|g|ml)", value.strip(), flags=re.IGNORECASE)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2).lower()
    if unit == "g":
        return num * 1000.0, "mg"
    return num, unit


def validate_triple(
    triple: dict[str, Any],
    ref_triples: set[tuple[str, str, str]],
    dosage_ranges: dict[tuple[str, str], tuple[float, float]],
) -> dict[str, Any]:
    head = str(triple.get("head", ""))
    rel = str(triple.get("relation", ""))
    tail = str(triple.get("tail", ""))

    status = "valid"
    level = "none"
    reason = "matched-or-not-conflicting"

    if rel == "treats" and (head, "contraindicated_for", tail) in ref_triples:
        status = "conflict"
        level = "high"
        reason = "kg_contraindication_conflict"

    elif rel == "contraindicated_for" and (head, "treats", tail) in ref_triples:
        status = "conflict"
        level = "medium"
        reason = "kg_treatment_conflict"

    elif rel == "dosage":
        parsed = parse_dose(tail)
        if parsed is not None:
            dose, unit = parsed
            key = (head, unit)
            if key in dosage_ranges:
                lo, hi = dosage_ranges[key]
                if dose < lo or dose > hi:
                    status = "conflict"
                    level = "high"
                    reason = f"dosage_out_of_range({lo}-{hi}{unit})"

    out = dict(triple)
    out.update(
        {
            "validation_status": status,
            "conflict_level": level,
            "conflict_reason": reason,
        }
    )
    return out


def build_record_conflict_index(validated: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "record_id": "",
            "has_conflict": False,
            "max_conflict_level": "none",
            "conflict_reasons": [],
        }
    )
    level_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}

    for row in validated:
        rid = str(row.get("record_id", ""))
        if not rid:
            continue
        item = summary[rid]
        item["record_id"] = rid
        level = str(row.get("conflict_level", "none"))
        reason = str(row.get("conflict_reason", ""))
        if str(row.get("validation_status")) == "conflict":
            item["has_conflict"] = True
            if level_rank[level] > level_rank[item["max_conflict_level"]]:
                item["max_conflict_level"] = level
            if reason and reason not in item["conflict_reasons"]:
                item["conflict_reasons"].append(reason)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="KG validation for candidate triples")
    parser.add_argument("--input", required=True, help="Candidate triples (.json/.jsonl)")
    parser.add_argument("--kg", required=True, help="Reference KG triples (.json/.jsonl)")
    parser.add_argument("--output", required=True, help="Validated triples output (.jsonl)")
    parser.add_argument(
        "--record-summary-output",
        default="",
        help="Optional per-record conflict summary output (.jsonl)",
    )
    args = parser.parse_args()

    candidates = load_json_records(args.input)
    ref_triples, dosage_ranges = load_reference_kg(args.kg)

    validated = [validate_triple(c, ref_triples, dosage_ranges) for c in candidates]
    save_json_records(args.output, validated, as_jsonl=True)

    high = sum(1 for x in validated if x.get("conflict_level") == "high")
    medium = sum(1 for x in validated if x.get("conflict_level") == "medium")
    conflict = sum(1 for x in validated if x.get("validation_status") == "conflict")
    print(
        f"[kg-validator] triples={len(validated)} conflicts={conflict} high={high} medium={medium}"
    )

    if args.record_summary_output:
        summary = list(build_record_conflict_index(validated).values())
        save_json_records(args.record_summary_output, summary, as_jsonl=True)
        print(f"[kg-validator] record_summary={len(summary)} output={Path(args.record_summary_output)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
