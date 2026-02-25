#!/usr/bin/env python3
"""Lightweight SimPO training simulation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from .utils import load_jsonl, save_json
except ImportError:  # pragma: no cover
    from utils import load_jsonl, save_json


def pair_margin(chosen: str, rejected: str) -> float:
    chosen_len = max(len(chosen), 1)
    rejected_len = max(len(rejected), 1)
    length_balance = 1.0 - abs(chosen_len - rejected_len) / max(chosen_len, rejected_len)
    lexical_gap = 1.0 - (len(set(chosen.split()) & set(rejected.split())) / max(len(set(chosen.split())), 1))
    return max(0.0, min(1.0, 0.5 * length_balance + 0.5 * lexical_gap))


def main() -> int:
    parser = argparse.ArgumentParser(description="SimPO trainer (simulated)")
    parser.add_argument("--pref-file", default="data/clean/pref_seed_pairs.jsonl")
    parser.add_argument("--output-dir", default="checkpoints/simpo-baseline")
    parser.add_argument("--metrics-out", default="reports/training/simpo_metrics.json")
    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="simpo")
    args = parser.parse_args()

    pairs = load_jsonl(args.pref_file)
    margins = [pair_margin(str(p.get("chosen", "")), str(p.get("rejected", ""))) for p in pairs]
    avg_margin = sum(margins) / len(margins) if margins else 0.0

    base_score = 0.58
    aligned_score = min(0.97, base_score + 0.25 * avg_margin)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "method": "SimPO",
        "task": args.task,
        "simulation": True,
        "samples": len(pairs),
        "avg_margin": round(avg_margin, 6),
        "base_score": base_score,
        "aligned_score": round(aligned_score, 6),
        "score_gain": round(aligned_score - base_score, 6),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": args.config or None,
    }

    save_json(out_dir / "metadata.json", meta)
    save_json(args.metrics_out, meta)
    print(f"[simpo] samples={len(pairs)} gain={meta['score_gain']:.4f} checkpoint={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
