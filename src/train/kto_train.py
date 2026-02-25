#!/usr/bin/env python3
"""Optional KTO-style alignment simulation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    from .utils import load_jsonl, save_json
except ImportError:  # pragma: no cover
    from utils import load_jsonl, save_json


def main() -> int:
    parser = argparse.ArgumentParser(description="KTO trainer (simulated)")
    parser.add_argument("--pref-file", default="data/clean/pref_seed_pairs.jsonl")
    parser.add_argument("--output-dir", default="checkpoints/kto-baseline")
    parser.add_argument("--metrics-out", default="reports/training/kto_metrics.json")
    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="kto")
    args = parser.parse_args()

    pairs = load_jsonl(args.pref_file)
    good_signals = sum(1 for p in pairs if len(str(p.get("chosen", ""))) >= len(str(p.get("rejected", ""))))
    signal_ratio = good_signals / len(pairs) if pairs else 0.0

    base_score = 0.58
    aligned_score = min(0.94, base_score + 0.18 * signal_ratio)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "method": "KTO",
        "task": args.task,
        "simulation": True,
        "samples": len(pairs),
        "good_signal_ratio": round(signal_ratio, 6),
        "base_score": base_score,
        "aligned_score": round(aligned_score, 6),
        "score_gain": round(aligned_score - base_score, 6),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": args.config or None,
    }

    save_json(out_dir / "metadata.json", meta)
    save_json(args.metrics_out, meta)
    print(f"[kto] samples={len(pairs)} gain={meta['score_gain']:.4f} checkpoint={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
