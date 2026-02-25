#!/usr/bin/env python3
"""PII cleaner for medical QA records."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PII_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
    (
        "cn_phone",
        re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)"),
        "<PHONE>",
    ),
    ("landline", re.compile(r"(?<!\d)0\d{2,3}-?\d{7,8}(?!\d)"), "<PHONE>"),
    ("id_card_cn", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "<ID_CARD>"),
    ("bank_card", re.compile(r"(?<!\d)\d{16,19}(?!\d)"), "<BANK_CARD>"),
    ("url", re.compile(r"\bhttps?://[^\s]+"), "<URL>"),
]


def sanitize_text(text: str) -> tuple[str, Counter]:
    updated = text
    counter: Counter = Counter()
    for name, pattern, repl in PII_PATTERNS:
        updated, count = pattern.subn(repl, updated)
        if count:
            counter[name] += count
    return updated, counter


def sanitize_payload(
    payload: Any,
    text_fields: set[str],
    strict: bool,
    field_path: str = "",
) -> tuple[Any, Counter]:
    total: Counter = Counter()

    if isinstance(payload, str):
        should_clean = strict or field_path in text_fields or field_path.split(".")[-1] in text_fields
        if not should_clean:
            return payload, total
        updated, cnt = sanitize_text(payload)
        total.update(cnt)
        return updated, total

    if isinstance(payload, list):
        cleaned = []
        for i, item in enumerate(payload):
            child_path = f"{field_path}[{i}]"
            item_clean, cnt = sanitize_payload(item, text_fields, strict, child_path)
            cleaned.append(item_clean)
            total.update(cnt)
        return cleaned, total

    if isinstance(payload, dict):
        cleaned: dict[str, Any] = {}
        for key, value in payload.items():
            child_path = f"{field_path}.{key}" if field_path else key
            value_clean, cnt = sanitize_payload(value, text_fields, strict, child_path)
            cleaned[key] = value_clean
            total.update(cnt)
        return cleaned, total

    return payload, total


def load_records(path: Path) -> tuple[list[dict[str, Any]], str]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
                if isinstance(obj, dict):
                    rows.append(obj)
        return rows, "jsonl"

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)], "json"
        if isinstance(obj, dict):
            return [obj], "json"
        raise ValueError(f"Unsupported JSON root type: {type(obj)}")

    raise ValueError(f"Unsupported input extension: {path.suffix}")


def save_records(path: Path, rows: list[dict[str, Any]], fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jsonl":
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="PII cleaner for medical QA datasets.")
    parser.add_argument("--input", required=True, help="Input file (.json/.jsonl)")
    parser.add_argument("--output", required=True, help="Output file (.json/.jsonl)")
    parser.add_argument(
        "--fields",
        default="query,context,answer",
        help="Comma-separated fields to clean in non-strict mode",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Sanitize all string fields recursively",
    )
    parser.add_argument(
        "--report",
        default="",
        help="Optional path to write replacement statistics as JSON",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    text_fields = {x.strip() for x in args.fields.split(",") if x.strip()}

    rows, fmt = load_records(input_path)
    cleaned_rows: list[dict[str, Any]] = []
    total = Counter()
    for row in rows:
        cleaned, cnt = sanitize_payload(row, text_fields=text_fields, strict=args.strict)
        cleaned_rows.append(cleaned)
        total.update(cnt)

    save_records(output_path, cleaned_rows, fmt)
    print(f"[pii] input={len(rows)} output={len(cleaned_rows)} replacements={dict(total)}")

    if args.report:
        report_path = Path(args.report).resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(dict(total), f, ensure_ascii=False, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

