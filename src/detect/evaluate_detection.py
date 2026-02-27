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
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


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


def write_report(
    path: Path,
    details: list[dict[str, Any]],
    m: dict[str, float],
    meta: dict[str, Any] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = meta or {}
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
    ]

    if meta:
        lines.extend(
            [
                f"- LLM 回退开关: {meta.get('llm_fallback_enabled', False)}",
                f"- LLM 回退调用次数: {meta.get('llm_fallback_calls', 0)}",
                f"- LLM 回退提升次数: {meta.get('llm_fallback_promotions', 0)}",
            ]
        )

    lines.extend(
        [
        "",
        "## 样例明细（前10条）",
        "| id | expected | predicted | score |",
        "|---|---|---|---|",
        ]
    )

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
    parser.add_argument("--enable-llm-fallback", action="store_true", help="Use LLM judge fallback to promote risky cases")
    parser.add_argument("--llm-model", default="gpt-4o-mini")
    parser.add_argument("--llm-cache", default="reports/eval/judge_risk_cache.jsonl")
    parser.add_argument("--llm-min-confidence", type=float, default=0.70)
    parser.add_argument("--llm-max-calls", type=int, default=0, help="Limit fallback calls; 0 means unlimited")
    parser.add_argument(
        "--llm-trigger",
        default="pred_low",
        choices=["pred_low", "pred_low_or_medium"],
        help="When to invoke LLM fallback",
    )
    parser.add_argument("--llm-log-every", type=int, default=100, help="Progress interval for LLM fallback")
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

    llm_judge = None
    if args.enable_llm_fallback:
        try:
            from eval.llm_risk_judge import judge_risk as llm_judge  # type: ignore
        except ModuleNotFoundError:
            try:
                from llm_risk_judge import judge_risk as llm_judge  # type: ignore
            except ModuleNotFoundError as exc:
                raise RuntimeError("LLM fallback enabled but eval.llm_risk_judge is not available") from exc

    llm_calls = 0
    llm_promotions = 0
    preds = []
    total = len(benchmark)
    for idx, row in enumerate(benchmark, start=1):
        out = guard_answer(
            query=str(row.get("query", "")),
            answer=str(row.get("answer", "")),
            kg_path=args.kg,
        )
        predicted_risk = str(out.get("risk_level", "low"))
        base_predicted_risk = predicted_risk
        llm_risk = ""
        llm_conf = 0.0
        llm_reason = ""
        llm_used = False
        llm_promoted = False

        should_trigger = predicted_risk == "low" or (
            args.llm_trigger == "pred_low_or_medium" and predicted_risk in {"low", "medium"}
        )
        allowed_by_budget = args.llm_max_calls <= 0 or llm_calls < args.llm_max_calls
        if llm_judge and should_trigger and allowed_by_budget:
            llm_calls += 1
            llm_used = True
            decision = llm_judge(
                query=str(row.get("query", "")),
                answer=str(row.get("answer", "")),
                model=args.llm_model,
                cache_path=args.llm_cache,
            )
            llm_risk = decision.risk
            llm_conf = float(decision.confidence)
            llm_reason = decision.reason
            if llm_conf >= args.llm_min_confidence and RISK_ORDER.get(llm_risk, 0) > RISK_ORDER.get(predicted_risk, 0):
                predicted_risk = llm_risk
                llm_promotions += 1
                llm_promoted = True

        preds.append(
            {
                "id": row.get("id"),
                "split": split_of(row),
                "query": row.get("query", ""),
                "answer": row.get("answer", ""),
                "expected_risk": row.get("expected_risk", "low"),
                "base_predicted_risk": base_predicted_risk,
                "predicted_risk": predicted_risk,
                "risk_score": float(out.get("risk_score", 0.0)),
                "base_blocked": base_predicted_risk == "high",
                "blocked": predicted_risk == "high",
                "llm_used": llm_used,
                "llm_risk": llm_risk,
                "llm_confidence": llm_conf,
                "llm_reason": llm_reason,
                "llm_promoted": llm_promoted,
            }
        )
        if idx % 200 == 0:
            print(f"[detection-eval] progress={idx}/{total}")
        if args.enable_llm_fallback and args.llm_log_every > 0 and llm_calls > 0 and llm_calls % args.llm_log_every == 0:
            print(f"[detection-eval:llm-fallback] calls={llm_calls} promotions={llm_promotions}")

    m = metrics(preds)

    pred_path = Path(args.pred_output)
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    with pred_path.open("w", encoding="utf-8") as f:
        for row in preds:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_report(
        Path(args.report),
        preds,
        m,
        meta={
            "llm_fallback_enabled": bool(args.enable_llm_fallback),
            "llm_fallback_calls": llm_calls,
            "llm_fallback_promotions": llm_promotions,
        },
    )
    print(f"[detection-eval] samples={len(preds)} report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
