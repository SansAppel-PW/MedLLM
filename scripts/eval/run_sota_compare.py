#!/usr/bin/env python3
"""Run reproducible proxy comparison for T406.

Note: This script compares *system policies* under the same benchmark answers.
It does not claim to reproduce official full-model capabilities.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.detect.atomic_fact_extractor import extract_atomic_facts
from src.detect.nli_checker import classify_fact
from src.detect.retriever import load_knowledge_docs, retrieve
from src.detect.runtime_guard import guard_answer
from src.detect.whitebox_uncertainty import estimate_uncertainty


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


def whitebox_policy(answer: str) -> dict[str, Any]:
    w = estimate_uncertainty(answer)
    score = 0.65 * float(w["entropy_norm"]) + 0.35 * (1.0 - float(w["self_consistency"]))
    if score >= 0.55:
        level = "high"
    elif score >= 0.35:
        level = "medium"
    else:
        level = "low"
    return {
        "final_answer": answer,
        "risk_level": level,
        "risk_score": score,
        "blocked": level == "high",
    }


def retrieval_policy(query: str, answer: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    facts = extract_atomic_facts(answer) or [answer]
    contra = 0
    for fact in facts:
        top = retrieve(fact, docs, top_k=5, context_query=query)
        nli = classify_fact(fact, top)
        if nli.get("label") == "contradict":
            contra += 1
    rate = contra / max(len(facts), 1)
    if rate >= 0.45:
        level = "high"
    elif rate >= 0.20:
        level = "medium"
    else:
        level = "low"
    return {
        "final_answer": answer,
        "risk_level": level,
        "risk_score": rate,
        "blocked": level == "high",
    }


def raw_policy(answer: str) -> dict[str, Any]:
    return {
        "final_answer": answer,
        "risk_level": "low",
        "risk_score": 0.0,
        "blocked": False,
    }


def compute_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    tp = fp = tn = fn = 0
    blocked_risky = 0
    risky_total = 0
    for row in rows:
        gold_pos = row["expected_risk"] in POSITIVE_LEVELS
        pred_pos = row["predicted_risk"] in POSITIVE_LEVELS
        if gold_pos:
            risky_total += 1
            if row["blocked"]:
                blocked_risky += 1
        if gold_pos and pred_pos:
            tp += 1
        elif (not gold_pos) and pred_pos:
            fp += 1
        elif (not gold_pos) and (not pred_pos):
            tn += 1
        else:
            fn += 1

    acc = (tp + tn) / max(tp + fp + tn + fn, 1)
    recall = tp / max(tp + fn, 1)
    precision = tp / max(tp + fp, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    specificity = tn / max(tn + fp, 1)
    unsafe_pass_rate = fn / max(risky_total, 1)
    risky_block_rate = blocked_risky / max(risky_total, 1)
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "specificity": specificity,
        "unsafe_pass_rate": unsafe_pass_rate,
        "risky_block_rate": risky_block_rate,
        "balanced_score": acc + specificity - unsafe_pass_rate,
        "tp": float(tp),
        "fp": float(fp),
        "tn": float(tn),
        "fn": float(fn),
    }


def evaluate_system(
    benchmark: list[dict[str, Any]],
    name: str,
    runner: Any,
    log_every: int = 0,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    total = len(benchmark)
    for idx, row in enumerate(benchmark, start=1):
        query = str(row.get("query", ""))
        answer = str(row.get("answer", ""))
        expected = str(row.get("expected_risk", "low"))
        out = runner(row, query, answer)
        details.append(
            {
                "id": row.get("id"),
                "query": query,
                "answer": answer,
                "expected_risk": expected,
                "predicted_risk": out["risk_level"],
                "risk_score": float(out["risk_score"]),
                "blocked": bool(out["blocked"]),
            }
        )
        if log_every > 0 and idx % log_every == 0:
            print(f"[sota:{name}] progress={idx}/{total}")
    return compute_metrics(details), details


def main() -> int:
    parser = argparse.ArgumentParser(description="Run proxy SOTA comparison")
    parser.add_argument("--benchmark", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--kg", default="data/kg/real_medqa_reference_kb.jsonl")
    parser.add_argument("--report", default="reports/sota_compare.md")
    parser.add_argument("--csv", default="reports/thesis_assets/tables/sota_compare_metrics.csv")
    parser.add_argument("--details-dir", default="reports/thesis_assets/tables/sota_details")
    parser.add_argument("--max-samples", type=int, default=0)
    parser.add_argument("--log-every", type=int, default=0)
    parser.add_argument(
        "--ours-predictions",
        default="",
        help="Optional precomputed predictions jsonl for MedLLM-Hybrid (fields: id,predicted_risk,blocked,risk_score)",
    )
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
        print(f"[sota] split filter={sorted(include_splits)} samples={len(benchmark)}")
    if args.max_samples > 0 and len(benchmark) > args.max_samples:
        benchmark = benchmark[: args.max_samples]
        print(f"[sota] truncated benchmark to {len(benchmark)} samples")
    docs = load_knowledge_docs(Path(args.kg))

    ours_pred_map: dict[str, dict[str, Any]] = {}
    if args.ours_predictions:
        pred_path = Path(args.ours_predictions)
        if pred_path.exists():
            for row in load_jsonl(pred_path):
                rid = str(row.get("id", ""))
                if rid:
                    ours_pred_map[rid] = row

    systems = [
        ("HuatuoGPT-7B-Proxy (raw)", lambda _r, _q, a: raw_policy(a)),
        ("BioMistral-7B-Proxy (whitebox)", lambda _r, _q, a: whitebox_policy(a)),
        ("MedQA-RAG-Proxy (retrieval)", lambda _r, q, a: retrieval_policy(q, a, docs)),
    ]

    if ours_pred_map:
        systems.append(
            (
                "MedLLM-Hybrid (ours)",
                lambda r, _q, a: {
                    "risk_level": str(ours_pred_map.get(str(r.get("id", "")), {}).get("predicted_risk", "low")),
                    "risk_score": float(ours_pred_map.get(str(r.get("id", "")), {}).get("risk_score", 0.0)),
                    "blocked": bool(ours_pred_map.get(str(r.get("id", "")), {}).get("blocked", False)),
                    "final_answer": a,
                },
            )
        )
    else:
        systems.append(
            ("MedLLM-Hybrid (ours)", lambda _r, q, a: guard_answer(q, a, kg_path=args.kg))
        )

    results: list[dict[str, Any]] = []
    details_dir = Path(args.details_dir)
    details_dir.mkdir(parents=True, exist_ok=True)

    for name, runner in systems:
        metrics, details = evaluate_system(benchmark, name, runner, log_every=args.log_every)
        results.append({"name": name, **metrics})
        out_path = details_dir / f"{name.replace(' ', '_').replace('/', '_')}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for row in details:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    results.sort(key=lambda x: (x["unsafe_pass_rate"], -x["f1"], -x["accuracy"]))

    csv_path = Path(args.csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "specificity",
                "unsafe_pass_rate",
                "risky_block_rate",
                "balanced_score",
                "tp",
                "fp",
                "tn",
                "fn",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    report_lines = [
        "# 对标模型评测（代理复现实验）",
        "",
        "> 说明：本报告采用统一输入答案的“系统策略代理”比较，用于离线方法学对照；",
        "> 不代表官方 HuatuoGPT/BioMistral 完整能力，仅用于同口径复现实验与论文方法部分说明。",
        "",
        f"- Benchmark: `{args.benchmark}`",
        f"- Knowledge base: `{args.kg}`",
        f"- 样本数: {len(benchmark)}",
        "",
        "| 系统 | Accuracy | Recall | Specificity | Unsafe Pass Rate | Risky Block Rate | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in results:
        report_lines.append(
            f"| {row['name']} | {row['accuracy']:.4f} | {row['recall']:.4f} | {row['specificity']:.4f} | "
            f"{row['unsafe_pass_rate']:.4f} | {row['risky_block_rate']:.4f} | {row['f1']:.4f} |"
        )

    best_safety = min(results, key=lambda x: x["unsafe_pass_rate"]) if results else None
    best_balanced = max(results, key=lambda x: x["balanced_score"]) if results else None
    if best_safety:
        report_lines.extend(
            [
                "",
                "## 结论",
                f"- 安全优先口径：`{best_safety['name']}` 的高风险放行率最低（Unsafe Pass Rate = {best_safety['unsafe_pass_rate']:.4f}）。",
                f"- 平衡口径（Accuracy + Specificity - UnsafePass）：`{best_balanced['name']}` 最优（{best_balanced['balanced_score']:.4f}）。",
                "- 可作为论文中“系统级安全策略对比”的可复现实验。",
            ]
        )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps({"systems": len(results), "report": str(report_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
