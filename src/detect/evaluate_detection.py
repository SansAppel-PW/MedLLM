#!/usr/bin/env python3
"""Offline evaluation for detection pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .runtime_guard import guard_answer
except ImportError:  # pragma: no cover
    from runtime_guard import guard_answer


POSITIVE_LEVELS = {"high", "medium"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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


def write_report(path: Path, details: list[dict[str, Any]], m: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 幻觉检测离线评测报告",
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
        "| id | expected | predicted | score |",
        "|---|---|---|---|",
    ]

    for row in details[:10]:
        lines.append(
            f"| {row['id']} | {row['expected_risk']} | {row['predicted_risk']} | {row['risk_score']:.4f} |"
        )

    false_neg = [x for x in details if x["expected_risk"] in POSITIVE_LEVELS and x["predicted_risk"] not in POSITIVE_LEVELS]
    false_pos = [x for x in details if x["expected_risk"] not in POSITIVE_LEVELS and x["predicted_risk"] in POSITIVE_LEVELS]

    lines.extend(
        [
            "",
            "## 误判统计",
            f"- 高/中风险漏检（FN）: {len(false_neg)}",
            f"- 低风险误报（FP）: {len(false_pos)}",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate runtime guard with labeled benchmark")
    parser.add_argument("--benchmark", default="data/benchmark/med_hallu_benchmark.jsonl")
    parser.add_argument("--kg", default="data/kg/cmekg_demo.jsonl")
    parser.add_argument("--pred-output", default="reports/detection_predictions.jsonl")
    parser.add_argument("--report", default="reports/detection_eval.md")
    parser.add_argument("--max-samples", type=int, default=0, help="Evaluate first N samples if > 0")
    parser.add_argument(
        "--include-splits",
        default="",
        help="Comma-separated benchmark splits to evaluate (e.g. validation,test)",
    )
    args = parser.parse_args()

    benchmark = load_jsonl(Path(args.benchmark))
    include_splits = parse_split_spec(args.include_splits)
    if include_splits:
        benchmark = [row for row in benchmark if split_of(row) in include_splits]
        print(f"[detection-eval] split filter={sorted(include_splits)} samples={len(benchmark)}")
    if args.max_samples > 0 and len(benchmark) > args.max_samples:
        benchmark = benchmark[: args.max_samples]
        print(f"[detection-eval] truncated benchmark to {len(benchmark)} samples")
    preds = []
    total = len(benchmark)
    for idx, row in enumerate(benchmark, start=1):
        out = guard_answer(
            query=str(row.get("query", "")),
            answer=str(row.get("answer", "")),
            kg_path=args.kg,
        )
        preds.append(
            {
                "id": row.get("id"),
                "query": row.get("query", ""),
                "answer": row.get("answer", ""),
                "expected_risk": row.get("expected_risk", "low"),
                "predicted_risk": out.get("risk_level", "low"),
                "risk_score": float(out.get("risk_score", 0.0)),
                "blocked": bool(out.get("blocked", False)),
            }
        )
        if idx % 200 == 0:
            print(f"[detection-eval] progress={idx}/{total}")

    m = metrics(preds)

    pred_path = Path(args.pred_output)
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    with pred_path.open("w", encoding="utf-8") as f:
        for row in preds:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_report(Path(args.report), preds, m)
    print(f"[detection-eval] samples={len(preds)} report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
