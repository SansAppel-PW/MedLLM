#!/usr/bin/env python3
"""Evaluate detection labels with LLM-as-a-Judge risk classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from eval.llm_risk_judge import judge_risk


POSITIVE_LEVELS = {"high", "medium"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_split_spec(spec: str) -> set[str]:
    return {x.strip().lower() for x in (spec or "").split(",") if x.strip()}


def split_of(row: dict[str, Any]) -> str:
    meta = row.get("meta", {})
    if not isinstance(meta, dict):
        return ""
    return str(meta.get("split", "")).strip().lower()


def metrics(samples: list[dict[str, Any]]) -> dict[str, float]:
    tp = fp = tn = fn = 0
    for s in samples:
        pred_pos = s["predicted_risk"] in POSITIVE_LEVELS
        gold_pos = s["expected_risk"] in POSITIVE_LEVELS
        if pred_pos and gold_pos:
            tp += 1
        elif pred_pos and not gold_pos:
            fp += 1
        elif not pred_pos and not gold_pos:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    acc = (tp + tn) / max(tp + tn + fp + fn, 1)

    return {
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": acc,
    }


def write_report(path: Path, details: list[dict[str, Any]], m: dict[str, float], model: str, cache: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# LLM Risk Judge 评测报告",
        "",
        f"- Model: `{model}`",
        f"- Cache: `{cache}`",
        "",
        "## 指标",
        f"- Accuracy: {m['accuracy']:.4f}",
        f"- Precision: {m['precision']:.4f}",
        f"- Recall: {m['recall']:.4f}",
        f"- F1: {m['f1']:.4f}",
        f"- TP/FP/TN/FN: {m['tp']}/{m['fp']}/{m['tn']}/{m['fn']}",
        f"- FPR: {m['fp'] / max(m['fp'] + m['tn'], 1):.4f}",
        f"- FNR: {m['fn'] / max(m['fn'] + m['tp'], 1):.4f}",
        f"- 样本数: {len(details)}",
        "",
        "## 样例明细（前10条）",
        "| id | expected | predicted | confidence |",
        "|---|---|---|---:|",
    ]
    for row in details[:10]:
        lines.append(
            f"| {row['id']} | {row['expected_risk']} | {row['predicted_risk']} | {row.get('judge_confidence', 0.0):.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LLM risk judge evaluation")
    parser.add_argument("--benchmark", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--pred-output", default="reports/detection_predictions_llm_judge.jsonl")
    parser.add_argument("--report", default="reports/detection_eval_llm_judge.md")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--cache", default="reports/eval/judge_risk_cache.jsonl")
    parser.add_argument("--max-samples", type=int, default=200)
    parser.add_argument("--include-splits", default="validation,test")
    parser.add_argument("--log-every", type=int, default=50)
    args = parser.parse_args()

    benchmark = load_jsonl(Path(args.benchmark))
    include_splits = parse_split_spec(args.include_splits)
    if include_splits:
        benchmark = [row for row in benchmark if split_of(row) in include_splits]
    if args.max_samples > 0 and len(benchmark) > args.max_samples:
        benchmark = benchmark[: args.max_samples]

    preds: list[dict[str, Any]] = []
    total = len(benchmark)
    for idx, row in enumerate(benchmark, start=1):
        decision = judge_risk(
            query=str(row.get("query", "")),
            answer=str(row.get("answer", "")),
            model=args.model,
            cache_path=args.cache,
        )
        preds.append(
            {
                "id": row.get("id"),
                "query": row.get("query", ""),
                "answer": row.get("answer", ""),
                "expected_risk": row.get("expected_risk", "low"),
                "predicted_risk": decision.risk,
                "judge_confidence": decision.confidence,
                "judge_reason": decision.reason,
            }
        )
        if args.log_every > 0 and idx % args.log_every == 0:
            print(f"[llm-risk-judge] progress={idx}/{total}")

    m = metrics(preds)

    pred_path = Path(args.pred_output)
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    with pred_path.open("w", encoding="utf-8") as f:
        for row in preds:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_report(Path(args.report), preds, m, model=args.model, cache=args.cache)
    print(json.dumps({"samples": len(preds), "report": args.report, "accuracy": m["accuracy"], "f1": m["f1"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
