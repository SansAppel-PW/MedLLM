#!/usr/bin/env python3
"""Audit benchmark construction artifacts that may bias detection metrics."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ANSWER_PREFIX_RE = re.compile(r"(?:正确答案|correct answer)\s*[:：]?\s*", flags=re.IGNORECASE)
OPTION_LETTER_RE = re.compile(r"^\s*([A-D])(?:[.\)\s]|$)", flags=re.IGNORECASE)


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


def has_option_letter(answer: str) -> bool:
    stripped = ANSWER_PREFIX_RE.sub("", answer or "")
    return bool(OPTION_LETTER_RE.match(stripped))


def classify_gap(gap: float) -> str:
    if gap >= 0.60:
        return "HIGH"
    if gap >= 0.30:
        return "MEDIUM"
    return "LOW"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit benchmark artifacts")
    parser.add_argument("--benchmark", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--include-splits", default="validation,test")
    parser.add_argument("--report", default="reports/thesis_support/benchmark_artifact_report.md")
    parser.add_argument("--json", default="reports/thesis_support/benchmark_artifact_report.json")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.benchmark))
    include_splits = parse_split_spec(args.include_splits)
    if include_splits:
        rows = [row for row in rows if split_of(row) in include_splits]

    by_risk = defaultdict(lambda: Counter(total=0, has_prefix=0, has_option_letter=0))
    for row in rows:
        risk = str(row.get("expected_risk", "low")).strip().lower()
        answer = str(row.get("answer", ""))
        slot = by_risk[risk]
        slot["total"] += 1
        if ANSWER_PREFIX_RE.search(answer):
            slot["has_prefix"] += 1
        if has_option_letter(answer):
            slot["has_option_letter"] += 1

    low_total = max(by_risk["low"]["total"], 1)
    high_total = max(by_risk["high"]["total"], 1)
    low_letter_rate = by_risk["low"]["has_option_letter"] / low_total
    high_letter_rate = by_risk["high"]["has_option_letter"] / high_total
    letter_gap = abs(low_letter_rate - high_letter_rate)
    leakage_risk = classify_gap(letter_gap)

    report_lines = [
        "# Benchmark Artifact Audit",
        "",
        f"- Benchmark: `{args.benchmark}`",
        f"- Splits: `{args.include_splits}`",
        f"- Samples: {len(rows)}",
        "",
        "| Risk Label | Count | Prefix Rate | Option-Letter Rate |",
        "|---|---:|---:|---:|",
    ]
    for risk in ["low", "medium", "high"]:
        slot = by_risk[risk]
        total = max(slot["total"], 1)
        report_lines.append(
            f"| {risk} | {slot['total']} | {slot['has_prefix'] / total:.4f} | {slot['has_option_letter'] / total:.4f} |"
        )

    report_lines.extend(
        [
            "",
            f"- Option-letter rate gap (low vs high): {letter_gap:.4f}",
            f"- Artifact leakage risk: **{leakage_risk}**",
            "",
            "## Interpretation",
            "- HIGH: answer format strongly correlates with label; detection metrics may be inflated.",
            "- MEDIUM: moderate correlation; report as potential bias and add robustness ablation.",
            "- LOW: no obvious answer-format shortcut at this level.",
        ]
    )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    out_json = {
        "benchmark": args.benchmark,
        "splits": sorted(include_splits),
        "samples": len(rows),
        "by_risk": {
            risk: {
                "count": int(slot["total"]),
                "prefix_rate": slot["has_prefix"] / max(slot["total"], 1),
                "option_letter_rate": slot["has_option_letter"] / max(slot["total"], 1),
            }
            for risk, slot in by_risk.items()
        },
        "option_letter_gap_low_high": letter_gap,
        "artifact_leakage_risk": leakage_risk,
    }
    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"samples": len(rows), "leakage_risk": leakage_risk, "gap": letter_gap}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
