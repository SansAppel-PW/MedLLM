#!/usr/bin/env python3
"""Append latest iteration report into a reusable decision log."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def decide(entry: dict[str, Any]) -> str:
    real_data = entry.get("real_data_summary", {})
    align = entry.get("real_alignment_summary", {})
    train_count = int(real_data.get("train_count", 0) or 0)
    dpo_pairs = int(align.get("dpo_pair_count", 0) or 0)
    if train_count >= 200 and dpo_pairs > 0:
        return "保持 real-data + real-DPO 路径，下一步优先申请 GPU 推进 Layer-B Qwen7B 主实验。"
    return "优先补足真实数据或 real alignment 证据，再进入主实验结论阶段。"


def build_log_entry(iteration: dict[str, Any]) -> dict[str, Any]:
    return {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_tag": iteration.get("run_tag"),
        "iteration_generated_at_utc": iteration.get("generated_at_utc"),
        "small_real_summary": iteration.get("small_real_summary", {}),
        "real_data_summary": iteration.get("real_data_summary", {}),
        "real_alignment_summary": iteration.get("real_alignment_summary", {}),
        "risk_assessment": iteration.get("risk_assessment", []),
        "next_min_loop": iteration.get("next_min_loop", []),
        "decision": decide(iteration),
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Decision Log",
        "",
        "| 记录时间(UTC) | Run Tag | real train/dev/test | DPO 对数 | 最优对齐 | 决策 |",
        "|---|---|---|---:|---|---|",
    ]
    for row in reversed(rows[-30:]):
        real_data = row.get("real_data_summary", {})
        align = row.get("real_alignment_summary", {})
        train = int(real_data.get("train_count", 0) or 0)
        dev = int(real_data.get("dev_count", 0) or 0)
        test = int(real_data.get("test_count", 0) or 0)
        dpo_pairs = int(align.get("dpo_pair_count", 0) or 0)
        best_method = align.get("best_method") or "-"
        decision = str(row.get("decision", "")).replace("|", "/")
        lines.append(
            f"| {row.get('iteration_generated_at_utc')} | {row.get('run_tag')} | {train}/{dev}/{test} | {dpo_pairs} | {best_method} | {decision} |"
        )

    if rows:
        latest = rows[-1]
        lines.extend(["", "## Latest Decision", f"- {latest.get('decision', '')}", "", "## Next Minimal Loop"])
        for step in latest.get("next_min_loop", []):
            lines.append(f"- {step}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update reusable decision log from latest iteration report")
    parser.add_argument("--iteration-json", default="reports/iteration/latest_iteration_report.json")
    parser.add_argument("--out-jsonl", default="reports/iteration/decision_log.jsonl")
    parser.add_argument("--out-md", default="reports/iteration/decision_log.md")
    args = parser.parse_args()

    iteration_path = Path(args.iteration_json)
    if not iteration_path.exists():
        raise SystemExit(f"missing iteration report: {iteration_path}")

    iteration = load_json(iteration_path)
    rows = load_jsonl(Path(args.out_jsonl))
    key = (iteration.get("run_tag"), iteration.get("generated_at_utc"))
    exists = any((x.get("run_tag"), x.get("iteration_generated_at_utc")) == key for x in rows)
    if not exists:
        rows.append(build_log_entry(iteration))

    write_jsonl(Path(args.out_jsonl), rows)
    write_markdown(Path(args.out_md), rows)
    print(f"[decision-log] entries={len(rows)} jsonl={args.out_jsonl} md={args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
