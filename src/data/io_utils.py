#!/usr/bin/env python3
"""Common IO helpers for JSON/JSONL records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def load_json_records(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with p.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {p}:{line_no}: {exc}") from exc
                if isinstance(obj, dict):
                    rows.append(obj)
        return rows

    if suffix == ".json":
        with p.open("r", encoding="utf-8") as f:
            obj = json.load(f)

        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
        if isinstance(obj, dict):
            # Try common wrappers.
            for key in ("data", "items", "records"):
                val = obj.get(key)
                if isinstance(val, list):
                    return [x for x in val if isinstance(x, dict)]
            return [obj]

    raise ValueError(f"Unsupported file format for {p}")


def save_json_records(path: str | Path, rows: Iterable[dict[str, Any]], as_jsonl: bool = True) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if as_jsonl or p.suffix.lower() == ".jsonl":
        with p.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return

    rows_list = list(rows)
    with p.open("w", encoding="utf-8") as f:
        json.dump(rows_list, f, ensure_ascii=False, indent=2)


def ensure_jsonl(path: str | Path) -> Path:
    p = Path(path)
    if p.suffix.lower() != ".jsonl":
        return p.with_suffix(p.suffix + ".jsonl")
    return p
