#!/usr/bin/env python3
"""Lightweight DPO training simulation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from .utils import load_jsonl, save_json
except ImportError:  # pragma: no cover
    from utils import load_jsonl, save_json


def pair_difficulty(chosen: str, rejected: str) -> float:
    if not chosen and not rejected:
        return 0.0
    overlap = len(set(chosen.split()) & set(rejected.split()))
    denom = max(len(set(chosen.split()) | set(rejected.split())), 1)
    similarity = overlap / denom
    return 1.0 - similarity


def main() -> int:
    parser = argparse.ArgumentParser(description="DPO trainer (simulated)")
    parser.add_argument("--pref-file", default="data/clean/pref_seed_pairs.jsonl")
    parser.add_argument("--output-dir", default="checkpoints/dpo-baseline")
    parser.add_argument("--metrics-out", default="reports/training/dpo_metrics.json")
    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="dpo")
    args = parser.parse_args()

    pairs = load_jsonl(args.pref_file)
    diffs = [pair_difficulty(str(p.get("chosen", "")), str(p.get("rejected", ""))) for p in pairs]
    avg_diff = sum(diffs) / len(diffs) if diffs else 0.0

    base_score = 0.58
    aligned_score = min(0.95, base_score + 0.22 * avg_diff)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "method": "DPO",
        "task": args.task,
        "simulation": True,
        "samples": len(pairs),
        "avg_pair_difficulty": round(avg_diff, 6),
        "base_score": base_score,
        "aligned_score": round(aligned_score, 6),
        "score_gain": round(aligned_score - base_score, 6),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": args.config or None,
    }

    save_json(out_dir / "metadata.json", meta)
    save_json(args.metrics_out, meta)
    print(f"[dpo] samples={len(pairs)} gain={meta['score_gain']:.4f} checkpoint={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
