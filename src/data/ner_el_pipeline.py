#!/usr/bin/env python3
"""Lightweight rule-based NER + entity linking pipeline.

Input: normalized QA records (json/jsonl)
Output: entity extraction results (jsonl)
"""

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


DEFAULT_TEXT_FIELDS = ["query", "context", "answer"]


def normalize_entity_type(value: str) -> str:
    v = (value or "").strip().lower()
    mapping = {
        "disease": "disease",
        "疾病": "disease",
        "drug": "drug",
        "药物": "drug",
        "symptom": "symptom",
        "症状": "symptom",
        "population": "population",
        "人群": "population",
        "condition": "condition",
    }
    return mapping.get(v, v or "unknown")


def load_kg_entity_catalog(kg_path: Path) -> dict[str, dict[str, str]]:
    rows = load_json_records(kg_path)
    entity_map: dict[str, dict[str, str]] = {}

    for row in rows:
        head = str(row.get("head", "")).strip()
        tail = str(row.get("tail", "")).strip()
        if head:
            entity_map.setdefault(
                head,
                {
                    "kb_id": str(row.get("head_id", f"ent:{head}")),
                    "type": normalize_entity_type(str(row.get("head_type", ""))),
                },
            )
        if tail:
            entity_map.setdefault(
                tail,
                {
                    "kb_id": str(row.get("tail_id", f"ent:{tail}")),
                    "type": normalize_entity_type(str(row.get("tail_type", ""))),
                },
            )

    return entity_map


def find_spans(text: str, term: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    if not text or not term:
        return spans

    pattern = re.escape(term)
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        spans.append((match.start(), match.end()))
    return spans


def extract_entities_from_text(
    text: str,
    field: str,
    entity_catalog: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    if not text.strip():
        return entities

    for term, meta in entity_catalog.items():
        spans = find_spans(text, term)
        for start, end in spans:
            entities.append(
                {
                    "text": term,
                    "type": meta.get("type", "unknown"),
                    "kb_id": meta.get("kb_id", f"ent:{term}"),
                    "field": field,
                    "start": start,
                    "end": end,
                }
            )

    # Add lightweight dosage entity extraction.
    dosage_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|g|ml)", flags=re.IGNORECASE)
    for m in dosage_pattern.finditer(text):
        entities.append(
            {
                "text": m.group(0),
                "type": "dosage",
                "kb_id": f"dosage:{m.group(1)}{m.group(2).lower()}",
                "field": field,
                "start": m.start(),
                "end": m.end(),
            }
        )

    return entities


def deduplicate_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for ent in entities:
        key = (
            ent.get("text"),
            ent.get("type"),
            ent.get("field"),
            ent.get("start"),
            ent.get("end"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ent)
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(description="Rule-based NER+EL pipeline")
    parser.add_argument("--input", required=True, help="Input records (.json/.jsonl)")
    parser.add_argument("--output", required=True, help="Output entities (.jsonl)")
    parser.add_argument("--kg", required=True, help="KG triples file (.json/.jsonl)")
    parser.add_argument(
        "--text-fields",
        default=",".join(DEFAULT_TEXT_FIELDS),
        help="Comma-separated fields to extract entities from",
    )
    args = parser.parse_args()

    input_rows = load_json_records(args.input)
    entity_catalog = load_kg_entity_catalog(Path(args.kg))
    fields = [x.strip() for x in args.text_fields.split(",") if x.strip()]

    out_rows = []
    type_counter = defaultdict(int)
    total_entities = 0

    for row in input_rows:
        record_id = str(row.get("id", ""))
        entities: list[dict[str, Any]] = []
        for field in fields:
            text = str(row.get(field, "") or "")
            entities.extend(extract_entities_from_text(text, field, entity_catalog))

        entities = deduplicate_entities(entities)
        for ent in entities:
            type_counter[ent.get("type", "unknown")] += 1
        total_entities += len(entities)

        out_rows.append(
            {
                "id": record_id,
                "entities": entities,
                "meta": {
                    "entity_count": len(entities),
                    "text_fields": fields,
                },
            }
        )

    save_json_records(args.output, out_rows, as_jsonl=True)
    summary = ", ".join([f"{k}:{v}" for k, v in sorted(type_counter.items())])
    print(f"[ner-el] records={len(out_rows)} entities={total_entities} by_type={summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
