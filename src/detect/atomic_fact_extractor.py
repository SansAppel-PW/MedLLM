#!/usr/bin/env python3
"""Atomic fact extraction for long medical answers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SPLIT_PATTERN = re.compile(r"[。！？!?；;\n]+")


def extract_atomic_facts(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    segments = []
    for chunk in SPLIT_PATTERN.split(text):
        chunk = chunk.strip(" ,，。；;：:\t")
        if not chunk:
            continue
        # Further split with conjunctions for finer facts.
        parts = re.split(r"(?:并且|同时|且|以及)", chunk)
        for p in parts:
            p = p.strip(" ,，。；;：:\t")
            if len(p) >= 4:
                segments.append(p)

    # Deduplicate while keeping order.
    deduped = []
    seen = set()
    for seg in segments:
        if seg in seen:
            continue
        seen.add(seg)
        deduped.append(seg)
    return deduped


def run_batch(input_path: Path, output_path: Path, field: str) -> None:
    rows = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    out = []
    for row in rows:
        rid = row.get("id")
        text = str(row.get(field, ""))
        facts = extract_atomic_facts(text)
        out.append({"id": rid, "facts": facts, "fact_count": len(facts)})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[facts] input={len(rows)} output={len(out)} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Atomic fact extractor")
    parser.add_argument("--text", default="", help="Single answer text")
    parser.add_argument("--input", default="", help="Batch input jsonl")
    parser.add_argument("--output", default="", help="Batch output jsonl")
    parser.add_argument("--field", default="answer", help="Text field")
    args = parser.parse_args()

    if args.text:
        print(json.dumps({"facts": extract_atomic_facts(args.text)}, ensure_ascii=False, indent=2))
        return 0

    if args.input and args.output:
        run_batch(Path(args.input), Path(args.output), args.field)
        return 0

    raise SystemExit("Use --text or (--input and --output)")


if __name__ == "__main__":
    raise SystemExit(main())
