#!/usr/bin/env python3
"""Build a format-balanced MedQA benchmark to reduce answer-style leakage."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OPTION_RE = re.compile(r"(?im)^\s*([A-D])[\.\)]\s*(.+?)\s*$")
ANSWER_PREFIX_RE = re.compile(r"(?:正确答案|correct answer)\s*[:：]?\s*", flags=re.IGNORECASE)
LETTER_RE = re.compile(r"^\s*([A-D])(?:[\.\)\s]|$)", flags=re.IGNORECASE)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\u4e00-\u9fff\s%.-]", "", text)
    return text.strip()


def parse_options(query: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for letter, text in OPTION_RE.findall(query or ""):
        key = (letter or "").upper()
        value = (text or "").strip()
        if key and value:
            out[key] = value
    return out


def parse_answer_letter(answer: str, options: dict[str, str]) -> tuple[str | None, str]:
    body = ANSWER_PREFIX_RE.sub("", answer or "").strip()
    m = LETTER_RE.match(body)
    if m:
        return m.group(1).upper(), "by_letter"

    body_norm = normalize_text(body)
    if not body_norm:
        return None, "unresolved_empty"

    # Prefer exact/containment matching first.
    for letter, option_text in options.items():
        opt_norm = normalize_text(option_text)
        if not opt_norm:
            continue
        if body_norm == opt_norm or body_norm in opt_norm or opt_norm in body_norm:
            return letter, "by_text_exact"

    # Fuzzy fallback for small formatting differences.
    best_letter = None
    best_score = 0.0
    for letter, option_text in options.items():
        ratio = difflib.SequenceMatcher(a=body_norm, b=normalize_text(option_text)).ratio()
        if ratio > best_score:
            best_score = ratio
            best_letter = letter
    if best_letter and best_score >= 0.78:
        return best_letter, "by_text_fuzzy"
    return None, "unresolved_no_match"


def split_of(row: dict[str, Any]) -> str:
    meta = row.get("meta", {})
    if not isinstance(meta, dict):
        return ""
    return str(meta.get("split", "")).strip().lower()


def has_option_letter(answer: str) -> bool:
    body = ANSWER_PREFIX_RE.sub("", answer or "", count=1).strip()
    return bool(LETTER_RE.match(body))


def build_balanced(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out: list[dict[str, Any]] = []
    stats = Counter(
        total=0,
        rewritten=0,
        unresolved=0,
        by_letter=0,
        by_text_exact=0,
        by_text_fuzzy=0,
        unresolved_empty=0,
        unresolved_no_match=0,
    )
    by_risk = defaultdict(Counter)

    for row in rows:
        stats["total"] += 1
        query = str(row.get("query", ""))
        answer = str(row.get("answer", ""))
        risk = str(row.get("expected_risk", "low")).strip().lower()
        split = split_of(row)
        options = parse_options(query)

        rewrite_mode = "unresolved_no_options"
        new_answer = answer
        selected_letter: str | None = None
        if options:
            selected_letter, rewrite_mode = parse_answer_letter(answer, options)
            if selected_letter and selected_letter in options:
                new_answer = f"正确答案: {selected_letter}. {options[selected_letter]}"
                stats[rewrite_mode] += 1
                if normalize_text(new_answer) != normalize_text(answer):
                    stats["rewritten"] += 1
            else:
                stats["unresolved"] += 1
                if rewrite_mode in {"unresolved_empty", "unresolved_no_match"}:
                    stats[rewrite_mode] += 1
        else:
            stats["unresolved"] += 1

        item = dict(row)
        meta = dict(item.get("meta", {})) if isinstance(item.get("meta"), dict) else {}
        meta.update(
            {
                "balanced_benchmark_v2": True,
                "rewrite_mode": rewrite_mode,
                "selected_option_letter": selected_letter or "",
                "answer_had_option_letter_before": has_option_letter(answer),
            }
        )
        item["meta"] = meta
        item["answer"] = new_answer
        out.append(item)

        by_risk[(risk, split)]["count"] += 1
        by_risk[(risk, split)]["letter_rate_after"] += 1 if has_option_letter(new_answer) else 0

    # finalize rates
    risk_summary: dict[str, Any] = {}
    for (risk, split), counter in sorted(by_risk.items()):
        key = f"{risk}:{split or 'nosplit'}"
        count = max(counter["count"], 1)
        risk_summary[key] = {
            "count": int(counter["count"]),
            "letter_rate_after": counter["letter_rate_after"] / count,
        }

    summary = {
        "total": stats["total"],
        "rewritten": stats["rewritten"],
        "unresolved": stats["unresolved"],
        "by_letter": stats["by_letter"],
        "by_text_exact": stats["by_text_exact"],
        "by_text_fuzzy": stats["by_text_fuzzy"],
        "unresolved_empty": stats["unresolved_empty"],
        "unresolved_no_match": stats["unresolved_no_match"],
        "risk_split_letter_rate_after": risk_summary,
    }
    return out, summary


def write_report(path: Path, summary: dict[str, Any], output_path: str) -> None:
    lines = [
        "# Balanced Detection Benchmark v2 Report",
        "",
        f"- Output: `{output_path}`",
        f"- Total rows: {summary.get('total', 0)}",
        f"- Rewritten rows: {summary.get('rewritten', 0)}",
        f"- Unresolved rows: {summary.get('unresolved', 0)}",
        "",
        "## Rewrite Modes",
        f"- by_letter: {summary.get('by_letter', 0)}",
        f"- by_text_exact: {summary.get('by_text_exact', 0)}",
        f"- by_text_fuzzy: {summary.get('by_text_fuzzy', 0)}",
        f"- unresolved_empty: {summary.get('unresolved_empty', 0)}",
        f"- unresolved_no_match: {summary.get('unresolved_no_match', 0)}",
        "",
        "## Option-Letter Rate After Rewrite",
        "| risk:split | count | option_letter_rate_after |",
        "|---|---:|---:|",
    ]
    risk_summary = summary.get("risk_split_letter_rate_after", {})
    for key in sorted(risk_summary):
        item = risk_summary[key]
        lines.append(f"| {key} | {item.get('count', 0)} | {item.get('letter_rate_after', 0.0):.4f} |")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build balanced detection benchmark v2")
    parser.add_argument("--input", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--output", default="data/benchmark/real_medqa_benchmark_v2_balanced.jsonl")
    parser.add_argument("--report", default="reports/benchmark_v2_balanced_report.md")
    parser.add_argument("--summary-json", default="reports/benchmark_v2_balanced_summary.json")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    out_rows, summary = build_balanced(rows)
    save_jsonl(Path(args.output), out_rows)
    write_report(Path(args.report), summary, args.output)

    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"output": args.output, **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
