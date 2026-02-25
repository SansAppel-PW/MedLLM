#!/usr/bin/env python3
"""Rewrite low/medium conflict samples and drop high-risk conflicts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    from .io_utils import load_json_records, save_json_records
except ImportError:  # pragma: no cover
    from io_utils import load_json_records, save_json_records


def group_conflicts_by_record(validated_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    level_rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    out: dict[str, dict[str, Any]] = {}

    for row in validated_rows:
        rid = str(row.get("record_id", ""))
        if not rid:
            continue
        level = str(row.get("conflict_level", "none"))
        reason = str(row.get("conflict_reason", ""))
        if rid not in out:
            out[rid] = {
                "max_level": "none",
                "reasons": [],
                "triples": [],
            }
        out[rid]["triples"].append(row)
        if reason and reason not in out[rid]["reasons"]:
            out[rid]["reasons"].append(reason)
        if level_rank[level] > level_rank[out[rid]["max_level"]]:
            out[rid]["max_level"] = level

    return out


def rewrite_answer(answer: str, reasons: list[str]) -> str:
    hint = "；".join(reasons[:2]) if reasons else "检测到潜在逻辑冲突"
    safe_suffix = (
        "\n\n[安全修订提示] 检测到原回答可能存在医学事实冲突（"
        + hint
        + "）。请以临床指南与专业医生建议为准。"
    )
    return (answer or "").strip() + safe_suffix


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite low/medium conflict records")
    parser.add_argument("--input", required=True, help="Normalized records (.json/.jsonl)")
    parser.add_argument("--validated", required=True, help="Validated triples (.json/.jsonl)")
    parser.add_argument("--output", required=True, help="Cleaned output records (.jsonl)")
    parser.add_argument("--rewrite-log", required=True, help="Rewrite audit log (.jsonl)")
    args = parser.parse_args()

    rows = load_json_records(args.input)
    validated = load_json_records(args.validated)
    conflict_index = group_conflicts_by_record(validated)

    cleaned: list[dict[str, Any]] = []
    rewrite_logs: list[dict[str, Any]] = []

    dropped = 0
    rewritten = 0
    untouched = 0

    for row in rows:
        rid = str(row.get("id", ""))
        conflict = conflict_index.get(rid, {"max_level": "none", "reasons": []})
        level = str(conflict.get("max_level", "none"))
        reasons = list(conflict.get("reasons", []))

        if level == "high":
            dropped += 1
            rewrite_logs.append(
                {
                    "id": rid,
                    "action": "drop",
                    "conflict_level": level,
                    "reasons": reasons,
                }
            )
            continue

        out_row = dict(row)
        if level in {"low", "medium"}:
            out_row["answer"] = rewrite_answer(str(out_row.get("answer", "")), reasons)
            rewritten += 1
            rewrite_logs.append(
                {
                    "id": rid,
                    "action": "rewrite",
                    "conflict_level": level,
                    "reasons": reasons,
                }
            )
        else:
            untouched += 1

        out_row.setdefault("meta", {})
        out_row["meta"]["conflict_level"] = level
        out_row["meta"]["conflict_reasons"] = reasons
        cleaned.append(out_row)

    save_json_records(args.output, cleaned, as_jsonl=True)
    save_json_records(args.rewrite_log, rewrite_logs, as_jsonl=True)

    print(
        f"[rewrite] input={len(rows)} output={len(cleaned)} "
        f"dropped={dropped} rewritten={rewritten} untouched={untouched}"
    )
    print(f"[rewrite] log={Path(args.rewrite_log)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
