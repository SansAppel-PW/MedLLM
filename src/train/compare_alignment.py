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

    rows.sort(key=lambda x: float(x.get("aligned_score", 0.0)), reverse=True)
    real_mode = any(not bool(x.get("simulation", True)) for x in rows)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# 对齐训练对比报告",
        "",
        (
            "> 说明：本报告包含真实训练指标。"
            if real_mode
            else "> 说明：本报告基于离线代理指标比较，不等同于真实大模型参数训练效果。"
        ),
        "",
        "| 方法 | 样本数 | 对齐后分数 | 提升 |",
        "|---|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            f"| {row.get('method')} | {row.get('samples', 0)} | "
            f"{float(row.get('aligned_score', 0.0)):.4f} | {float(row.get('score_gain', 0.0)):.4f} |"
        )

    if rows:
        best = rows[0]
        lines.extend(
            [
                "",
                "## 结论",
                f"当前最佳方法: **{best.get('method')}**，对齐后分数 {float(best.get('aligned_score', 0.0)):.4f}。",
            ]
        )
    else:
        lines.extend(["", "## 结论", "暂无可对比结果。"])

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[alignment-compare] methods={len(rows)} report={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
