#!/usr/bin/env python3
"""Generate structured error analysis report from detection predictions."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


POSITIVE_LEVELS = {"high", "medium"}
UNCERTAIN_HINTS = {"可能", "不确定", "maybe", "uncertain", "likely", "perhaps"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_benchmark_index(path: Path) -> dict[str, dict[str, str]]:
    idx: dict[str, dict[str, str]] = {}
    if not path.exists():
        return idx
    for row in load_jsonl(path):
        rid = str(row.get("id", ""))
        idx[rid] = {
            "query": str(row.get("query", "")),
            "answer": str(row.get("answer", "")),
        }
    return idx


def clip(text: str, limit: int = 120) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 3] + "..."


def classify_error(row: dict[str, Any]) -> tuple[str, str]:
    expected = str(row.get("expected_risk", "low"))
    predicted = str(row.get("predicted_risk", "low"))
    query = str(row.get("query", ""))
    answer = str(row.get("answer", ""))
    risk_score = float(row.get("risk_score", 0.0))
    lowered = answer.lower()

    if expected in POSITIVE_LEVELS and predicted not in POSITIVE_LEVELS:
        err_type = "漏检"
        if "选项" in query and "正确答案" in answer:
            reason = "选项错配未识别"
        elif 0.28 <= risk_score <= 0.36:
            reason = "阈值边界样本"
        else:
            reason = "证据检索覆盖不足"
        return err_type, reason

    err_type = "误报"
    if any(k in lowered for k in UNCERTAIN_HINTS):
        reason = "不确定措辞触发风险"
    elif len(answer) > 200:
        reason = "长答案熵值偏高"
    elif "正确答案" in answer and "选项" in query:
        reason = "选项类样本检索噪声"
    else:
        reason = "规则融合误判"
    return err_type, reason


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate error analysis report")
    parser.add_argument("--predictions", default="reports/detection_predictions.jsonl")
    parser.add_argument("--output", default="reports/error_analysis.md")
    parser.add_argument("--cases-out", default="reports/thesis_assets/cases/error_cases_top30.jsonl")
    parser.add_argument("--top-n", type=int, default=30)
    parser.add_argument("--benchmark", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument(
        "--supplement-glob",
        default="reports/thesis_assets/tables/sota_details/*.jsonl",
        help="Use extra prediction files if primary errors are fewer than top-n",
    )
    args = parser.parse_args()

    benchmark_idx = build_benchmark_index(Path(args.benchmark))
    rows = load_jsonl(Path(args.predictions))

    errors: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def collect_errors(rows_in: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in rows_in:
            expected = str(row.get("expected_risk", "low"))
            predicted = str(row.get("predicted_risk", "low"))
            correct = (expected in POSITIVE_LEVELS) == (predicted in POSITIVE_LEVELS)
            if correct:
                continue

            rid = str(row.get("id", ""))
            key = (source, rid)
            if key in seen:
                continue
            seen.add(key)

            err_type, reason = classify_error(row)
            severity = float(row.get("risk_score", 0.0))
            if expected in POSITIVE_LEVELS and predicted not in POSITIVE_LEVELS:
                # For FN, lower score means the model is more overconfidently wrong.
                severity = 1.0 - severity

            query = str(row.get("query", ""))
            answer = str(row.get("answer", ""))
            if (not query or not answer) and rid in benchmark_idx:
                query = benchmark_idx[rid]["query"]
                answer = benchmark_idx[rid]["answer"]

            out.append(
                {
                    "id": rid,
                    "source": source,
                    "type": err_type,
                    "reason": reason,
                    "expected_risk": expected,
                    "predicted_risk": predicted,
                    "risk_score": float(row.get("risk_score", 0.0)),
                    "severity": severity,
                    "query": query,
                    "answer": answer,
                }
            )
        return out

    errors.extend(collect_errors(rows, source="medllm_hybrid"))

    if len(errors) < max(args.top_n, 1) and args.supplement_glob:
        for p_str in sorted(glob.glob(args.supplement_glob)):
            p = Path(p_str)
            errors.extend(collect_errors(load_jsonl(p), source=p.stem))
            if len(errors) >= max(args.top_n, 1):
                break

    errors.sort(key=lambda x: x["severity"], reverse=True)
    top_cases = errors[: max(args.top_n, 1)]

    type_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for e in errors:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
        reason_counts[e["reason"]] = reason_counts.get(e["reason"], 0) + 1
        source_counts[e["source"]] = source_counts.get(e["source"], 0) + 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 错误案例分析",
        "",
        "## 总体统计",
        f"- 主预测文件样本数: {len(rows)}",
        f"- 误判总数: {len(errors)}",
        f"- 漏检数: {type_counts.get('漏检', 0)}",
        f"- 误报数: {type_counts.get('误报', 0)}",
        "",
        "## 误判来源分布",
    ]
    for k, v in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {k}: {v}")

    lines.extend(["", "## 误判原因分布"])
    for k, v in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {k}: {v}")

    lines.extend(
        [
            "",
            f"## Top {len(top_cases)} 失败案例",
            "| id | 来源 | 类型 | 期望 | 预测 | 分数 | 归因 | 问题摘要 | 回答摘要 |",
            "|---|---|---|---|---|---:|---|---|---|",
        ]
    )

    for c in top_cases:
        lines.append(
            f"| {c['id']} | {c['source']} | {c['type']} | {c['expected_risk']} | {c['predicted_risk']} | "
            f"{c['risk_score']:.4f} | {c['reason']} | {clip(str(c['query']))} | {clip(str(c['answer']))} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cases_out = Path(args.cases_out)
    cases_out.parent.mkdir(parents=True, exist_ok=True)
    with cases_out.open("w", encoding="utf-8") as f:
        for c in top_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "rows": len(rows),
                "errors": len(errors),
                "top_cases": len(top_cases),
                "output": str(output_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
