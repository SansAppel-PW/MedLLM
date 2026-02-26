#!/usr/bin/env python3
"""Build baseline comparison table for small-real experiments."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build small-real baseline comparison table")
    parser.add_argument("--base-metrics", required=True)
    parser.add_argument("--tuned-metrics", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    base = load_json(Path(args.base_metrics))
    tuned = load_json(Path(args.tuned_metrics))

    rows = [
        {
            "model": "TinyGPT2-Base",
            "mode": "zero_shot_base",
            "samples": base.get("samples", 0),
            "exact_match": float(base.get("exact_match", 0.0)),
            "rouge_l_f1": float(base.get("rouge_l_f1", 0.0)),
            "char_f1": float(base.get("char_f1", 0.0)),
        },
        {
            "model": "TinyGPT2-LoRA",
            "mode": "small_real_lora",
            "samples": tuned.get("samples", 0),
            "exact_match": float(tuned.get("exact_match", 0.0)),
            "rouge_l_f1": float(tuned.get("rouge_l_f1", 0.0)),
            "char_f1": float(tuned.get("char_f1", 0.0)),
        },
    ]

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["model", "mode", "samples", "exact_match", "rouge_l_f1", "char_f1"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    md_lines = [
        "# Small Real Baseline Compare",
        "",
        "| Model | Mode | Samples | Exact Match | Rouge-L F1 | Char F1 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        md_lines.append(
            "| {model} | {mode} | {samples} | {exact_match:.6f} | {rouge_l_f1:.6f} | {char_f1:.6f} |".format(
                **row
            )
        )
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[baseline-table] csv={args.out_csv} md={args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
