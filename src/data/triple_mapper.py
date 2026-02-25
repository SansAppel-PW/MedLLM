#!/usr/bin/env python3
"""Map QA records + extracted entities into candidate medical triples."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

try:
    from .io_utils import load_json_records, save_json_records
except ImportError:  # pragma: no cover
    from io_utils import load_json_records, save_json_records


RELATION_PATTERNS = {
    "contraindicated_for": ["禁忌", "禁用", "避免", "不宜"],
    "treats": ["治疗", "用于", "缓解", "适用于"],
    "dosage": ["剂量", "每次", "每日", "每4", "mg", "g", "ml"],
}


def entity_index(entity_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in entity_rows:
        rid = str(row.get("id", ""))
        out[rid] = list(row.get("entities", []))
    return out


def pick_first(entities: list[dict[str, Any]], ent_type: str) -> dict[str, Any] | None:
    for ent in entities:
        if ent.get("type") == ent_type:
            return ent
    return None


def infer_relations(text: str) -> list[str]:
    rels = []
    for rel, kws in RELATION_PATTERNS.items():
        if any(kw in text for kw in kws):
            rels.append(rel)
    return rels


def extract_dosage(text: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|ml)", text, flags=re.IGNORECASE)
    if not m:
        return ""
    value = float(m.group(1))
    unit = m.group(2).lower()
    if unit == "g":
        value *= 1000.0
        unit = "mg"
    return f"{value:.0f}{unit}" if value.is_integer() else f"{value:.2f}{unit}"


def map_record_to_triples(record: dict[str, Any], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rid = str(record.get("id", ""))
    query = str(record.get("query", "") or "")
    answer = str(record.get("answer", "") or "")
    merged = f"{query}\n{answer}"

    inferred_rels = infer_relations(merged)
    if not inferred_rels:
        inferred_rels = ["treats"]

    drug = pick_first(entities, "drug")
    disease = pick_first(entities, "disease")
    population = pick_first(entities, "population")

    triples: list[dict[str, Any]] = []
    for rel in inferred_rels:
        if rel == "dosage":
            dosage = extract_dosage(merged)
            if drug and dosage:
                triples.append(
                    {
                        "record_id": rid,
                        "head": drug.get("text"),
                        "head_type": "drug",
                        "relation": "dosage",
                        "tail": dosage,
                        "tail_type": "dosage",
                        "confidence": 0.85,
                    }
                )
            continue

        target = population or disease
        if drug and target:
            triples.append(
                {
                    "record_id": rid,
                    "head": drug.get("text"),
                    "head_type": "drug",
                    "relation": rel,
                    "tail": target.get("text"),
                    "tail_type": target.get("type"),
                    "confidence": 0.8,
                }
            )

    if not triples and drug and disease:
        triples.append(
            {
                "record_id": rid,
                "head": drug.get("text"),
                "head_type": "drug",
                "relation": "treats",
                "tail": disease.get("text"),
                "tail_type": "disease",
                "confidence": 0.5,
            }
        )

    return triples


def main() -> int:
    parser = argparse.ArgumentParser(description="Map normalized QA records into candidate triples")
    parser.add_argument("--input", required=True, help="Normalized records (.json/.jsonl)")
    parser.add_argument("--entities", required=True, help="NER+EL output (.json/.jsonl)")
    parser.add_argument("--output", required=True, help="Output candidate triples (.jsonl)")
    args = parser.parse_args()

    records = load_json_records(args.input)
    ent_rows = load_json_records(args.entities)
    ent_idx = entity_index(ent_rows)

    triples: list[dict[str, Any]] = []
    for row in records:
        rid = str(row.get("id", ""))
        triples.extend(map_record_to_triples(row, ent_idx.get(rid, [])))

    save_json_records(args.output, triples, as_jsonl=True)
    print(f"[triple-mapper] records={len(records)} triples={len(triples)} output={Path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
