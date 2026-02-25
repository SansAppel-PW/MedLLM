#!/usr/bin/env python3
"""White-box style uncertainty scoring (heuristic version)."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .common import has_any, tokenize
except ImportError:  # pragma: no cover
    from common import has_any, tokenize


UNCERTAIN_CUES = ["可能", "大概", "不确定", "或许", "建议咨询", "仅供参考"]
OVERCONFIDENT_CUES = ["绝对", "一定", "完全", "100%", "保证"]


def shannon_entropy(tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    freq = Counter(tokens)
    total = len(tokens)
    ent = 0.0
    for count in freq.values():
        p = count / total
        ent -= p * math.log(p, 2)
    return ent


def self_consistency_proxy(text: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.0
    uniq_ratio = len(set(tokens)) / max(len(tokens), 1)
    uncertain_penalty = 0.12 if has_any(text, UNCERTAIN_CUES) else 0.0
    overconf_penalty = 0.08 if has_any(text, OVERCONFIDENT_CUES) else 0.0
    score = 0.85 - (1.0 - uniq_ratio) * 0.3 - uncertain_penalty - overconf_penalty
    return max(0.0, min(1.0, score))


def eigenscore_proxy(tokens: list[str]) -> float:
    if len(tokens) < 2:
        return 0.0
    bigrams = list(zip(tokens[:-1], tokens[1:]))
    return len(set(bigrams)) / max(len(bigrams), 1)


def estimate_uncertainty(text: str) -> dict[str, float]:
    tokens = tokenize(text)
    entropy = shannon_entropy(tokens)
    self_consistency = self_consistency_proxy(text, tokens)
    eigenscore = eigenscore_proxy(tokens)

    # Scale entropy into [0,1] using a practical cap for short medical answers.
    entropy_norm = max(0.0, min(1.0, entropy / 3.5))
    uncertainty_score = max(0.0, min(1.0, 0.5 * entropy_norm + 0.5 * (1 - self_consistency)))

    return {
        "entropy": round(entropy, 6),
        "entropy_norm": round(entropy_norm, 6),
        "self_consistency": round(self_consistency, 6),
        "eigenscore": round(eigenscore, 6),
        "uncertainty_score": round(uncertainty_score, 6),
    }


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
        out.append({"id": rid, **estimate_uncertainty(text)})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[whitebox] input={len(rows)} output={len(out)} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="White-box uncertainty estimator")
    parser.add_argument("--text", default="", help="Single text input")
    parser.add_argument("--input", default="", help="Batch input jsonl")
    parser.add_argument("--output", default="", help="Batch output jsonl")
    parser.add_argument("--field", default="answer", help="Text field in batch mode")
    args = parser.parse_args()

    if args.text:
        print(json.dumps(estimate_uncertainty(args.text), ensure_ascii=False, indent=2))
        return 0

    if args.input and args.output:
        run_batch(Path(args.input), Path(args.output), args.field)
        return 0

    raise SystemExit("Use --text or (--input and --output)")


if __name__ == "__main__":
    raise SystemExit(main())
