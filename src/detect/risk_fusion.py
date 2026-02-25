#!/usr/bin/env python3
"""Fuse white-box and fact-check signals into final hallucination risk."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def index_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out = {}
    for row in rows:
        out[str(row.get("id", ""))] = row
    return out


def nli_stats(row: dict[str, Any]) -> dict[str, float]:
    results = row.get("fact_results", [])
    total = len(results)
    if total == 0:
        return {"fact_total": 0, "contradict_rate": 0.0, "entail_rate": 0.0}

    contradict = sum(1 for x in results if x.get("label") == "contradict")
    entail = sum(1 for x in results if x.get("label") == "entail")
    return {
        "fact_total": total,
        "contradict_rate": contradict / total,
        "entail_rate": entail / total,
    }


def risk_level(score: float, high: float, medium: float) -> str:
    if score >= high:
        return "high"
    if score >= medium:
        return "medium"
    return "low"


def fuse_one(
    rec_id: str,
    whitebox_row: dict[str, Any] | None,
    nli_row: dict[str, Any] | None,
    high: float,
    medium: float,
) -> dict[str, Any]:
    w = whitebox_row or {}
    n = nli_stats(nli_row or {})

    entropy_norm = float(w.get("entropy_norm", 0.0))
    self_consistency = float(w.get("self_consistency", 0.0))
    contradict_rate = float(n.get("contradict_rate", 0.0))
    overconfidence_flag = float(w.get("overconfidence_flag", 0.0))

    # In medical QA, contradiction evidence should dominate final risk.
    score = (
        0.12 * entropy_norm
        + 0.12 * (1.0 - self_consistency)
        + 0.66 * contradict_rate
        + 0.10 * overconfidence_flag
    )
    score = max(0.0, min(1.0, score))

    return {
        "id": rec_id,
        "risk_score": round(score, 6),
        "risk_level": risk_level(score, high, medium),
        "signals": {
            "entropy_norm": round(entropy_norm, 6),
            "self_consistency": round(self_consistency, 6),
            "contradict_rate": round(contradict_rate, 6),
            "fact_total": int(n.get("fact_total", 0)),
            "entail_rate": round(float(n.get("entail_rate", 0.0)), 6),
            "overconfidence_flag": round(overconfidence_flag, 6),
        },
    }


def run_batch(whitebox_path: Path, nli_path: Path, output_path: Path, high: float, medium: float) -> None:
    whitebox_rows = load_jsonl(whitebox_path)
    nli_rows = load_jsonl(nli_path)

    w_idx = index_by_id(whitebox_rows)
    n_idx = index_by_id(nli_rows)

    all_ids = sorted(set(w_idx.keys()) | set(n_idx.keys()))
    fused = [fuse_one(i, w_idx.get(i), n_idx.get(i), high, medium) for i in all_ids]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in fused:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[risk-fusion] input={len(all_ids)} output={len(fused)} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Risk fusion")
    parser.add_argument("--whitebox", required=True, help="whitebox jsonl")
    parser.add_argument("--nli", required=True, help="nli jsonl")
    parser.add_argument("--output", required=True, help="output jsonl")
    parser.add_argument("--high", type=float, default=0.45)
    parser.add_argument("--medium", type=float, default=0.30)
    args = parser.parse_args()

    run_batch(Path(args.whitebox), Path(args.nli), Path(args.output), args.high, args.medium)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
