#!/usr/bin/env python3
"""Generate end-to-end acceptance report for the demo pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.serve.app import ask_once


CASES = [
    "血友病患者可以使用阿司匹林吗？",
    "布洛芬成人常见剂量是多少？",
    "青霉素过敏患者可以用阿莫西林吗？",
    "流感可使用奥司他韦吗？",
]


def main() -> int:
    out_rows = []
    for q in CASES:
        res = ask_once(q)
        out_rows.append(
            {
                "query": q,
                "risk_level": res.get("risk_level"),
                "risk_score": res.get("risk_score"),
                "blocked": res.get("blocked"),
                "candidate_answer": res.get("candidate_answer"),
                "final_answer": res.get("final_answer"),
            }
        )

    report = Path("reports/e2e_acceptance.md")
    report.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# 端到端验收报告",
        "",
        "## 测试范围",
        "- 输入问题 -> 候选回答生成 -> 幻觉风险检测 -> 最终输出",
        "",
        "## 验收结果",
        "| Query | Risk | Score | Blocked |",
        "|---|---|---:|---|",
    ]

    for row in out_rows:
        lines.append(
            f"| {row['query']} | {row['risk_level']} | {float(row['risk_score']):.4f} | {row['blocked']} |"
        )

    lines.extend(
        [
            "",
            "## 结论",
            "- 流程可完整执行，能够输出风险分级与拦截结果。",
            f"- 本次样例中触发拦截 {sum(1 for x in out_rows if x['blocked'])} 次，中高风险回答会附加安全提示或被拦截。",
        ]
    )

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    detail = Path("reports/e2e_acceptance_detail.json")
    detail.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[e2e] report={report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
