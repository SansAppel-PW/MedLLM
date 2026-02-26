#!/usr/bin/env python3
"""Generate alignment comparison report across DPO/SimPO/KTO."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def metric_value(row: dict[str, Any]) -> float:
    if "aligned_score" in row:
        return float(row.get("aligned_score", 0.0))
    if "pref_accuracy_after" in row:
        return float(row.get("pref_accuracy_after", 0.0))
    return 0.0


def gain_value(row: dict[str, Any]) -> float:
    if "score_gain" in row:
        return float(row.get("score_gain", 0.0))
    if "pref_accuracy_gain" in row:
        return float(row.get("pref_accuracy_gain", 0.0))
    return 0.0


def sample_value(row: dict[str, Any]) -> int:
    if "samples" in row:
        return int(row.get("samples", 0))
    if "pair_count" in row:
        return int(row.get("pair_count", 0))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare alignment methods")
    parser.add_argument("--dpo", default="reports/training/dpo_metrics.json")
    parser.add_argument("--simpo", default="reports/training/simpo_metrics.json")
    parser.add_argument("--kto", default="reports/training/kto_metrics.json")
    parser.add_argument("--output", default="reports/alignment_compare.md")
    args = parser.parse_args()

    rows = []
    for path in [Path(args.dpo), Path(args.simpo), Path(args.kto)]:
        data = load_json(path)
        if not data:
            continue
        rows.append(data)

    rows.sort(key=metric_value, reverse=True)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# 对齐训练对比报告",
        "",
        "> 说明：本报告支持代理指标与真实偏好准确率混合展示，需在论文中明确口径。",
        "",
        "| 方法 | 类型 | 样本数 | 对齐后指标 | 提升 |",
        "|---|---|---:|---:|---:|",
    ]

    for row in rows:
        sim = row.get("simulation")
        mode = "proxy" if sim is True else ("real" if sim is False else "mixed")
        lines.append(
            f"| {row.get('method')} | {mode} | {sample_value(row)} | "
            f"{metric_value(row):.4f} | {gain_value(row):.4f} |"
        )

    if rows:
        best = rows[0]
        lines.extend(
            [
                "",
                "## 结论",
                f"当前最佳方法: **{best.get('method')}**，对齐后指标 {metric_value(best):.4f}。",
            ]
        )
    else:
        lines.extend(["", "## 结论", "暂无可对比结果。"])

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[alignment-compare] methods={len(rows)} report={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
