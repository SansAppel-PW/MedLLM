#!/usr/bin/env python3
"""Construct adversarial preference pairs for medical alignment."""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any

try:
    from .utils import load_jsonl, save_jsonl
except ImportError:  # pragma: no cover
    from utils import load_jsonl, save_jsonl


def build_replacement_map(kg_rows: list[dict[str, Any]]) -> dict[str, str]:
    treat_map = {}
    contra_map = {}
    for row in kg_rows:
        h = str(row.get("head", ""))
        r = str(row.get("relation", ""))
        t = str(row.get("tail", ""))
        if r == "treats":
            treat_map[h] = t
        if r == "contraindicated_for":
            contra_map[h] = t

    replacement = {}
    # If a drug has contraindication, replace with dangerous claim.
    for drug, population in contra_map.items():
        replacement[drug] = f"{drug}对{population}人群同样适用"

    for drug, disease in treat_map.items():
        replacement.setdefault(drug, f"{drug}不适用于{disease}")

    return replacement


def perturb_text(text: str, replacement_map: dict[str, str]) -> str:
    out = text
    for key, rep in replacement_map.items():
        if key in out:
            return out.replace(key, rep, 1)

    # Numeric perturbation fallback.
    m = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|ml)", out, flags=re.IGNORECASE)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        wrong = val * 10
        wrong_s = f"{wrong:.0f}" if wrong.is_integer() else f"{wrong:.2f}"
        return out[: m.start()] + f"{wrong_s}{unit}" + out[m.end() :]

    # Semantic fallback.
    flips = [("建议", "不建议"), ("可以", "不可以"), ("避免", "优先")]
    for a, b in flips:
        if a in out:
            return out.replace(a, b, 1)

    return out + "（忽略禁忌症）"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build hard negative preference pairs")
    parser.add_argument("--input", default="data/clean/sft_train.jsonl")
    parser.add_argument("--kg", default="data/kg/cmekg_demo.jsonl")
    parser.add_argument("--output", default="data/clean/pref_seed_pairs.jsonl")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    rows = load_jsonl(args.input)
    kg_rows = load_jsonl(args.kg)
    replacement_map = build_replacement_map(kg_rows)

    pairs = []
    for row in rows:
        query = str(row.get("query", ""))
        context = str(row.get("context", ""))
        prompt = query if not context else f"{query}\n\n上下文:\n{context}"
        chosen = str(row.get("answer", ""))
        rejected = perturb_text(chosen, replacement_map)
        pairs.append(
            {
                "id": row.get("id"),
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "meta": {
                    "strategy": "entity_replacement_or_numeric_perturbation",
                },
            }
        )

    save_jsonl(args.output, pairs)
    print(f"[hard-negative] input={len(rows)} output={len(pairs)} path={Path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
