#!/usr/bin/env python3
"""Convert heterogeneous medical QA data into a unified schema.

Unified schema:
{
  "id": "...",
  "query": "...",
  "context": "...",
  "answer": "...",
  "meta": {...}
}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

QUERY_ALIASES = [
    "query",
    "question",
    "instruction",
    "input",
    "prompt",
    "ask",
    "user_query",
]

CONTEXT_ALIASES = [
    "context",
    "history",
    "background",
    "patient_info",
    "clinical_context",
]

ANSWER_ALIASES = [
    "answer",
    "response",
    "output",
    "target",
    "assistant_answer",
    "final_answer",
    "label",
]

ID_ALIASES = ["id", "uid", "qid", "question_id", "uuid", "sample_id"]
CONVERSATION_ALIASES = ["messages", "conversation", "dialogue", "dialog", "conversations"]

ROLE_ALIASES = ["role", "from", "speaker"]
CONTENT_ALIASES = ["content", "text", "value", "utterance"]


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [_to_text(x) for x in value]
        return "\n".join([x for x in parts if x])
    if isinstance(value, dict):
        # Prefer text-like keys first, then fallback to json string.
        for key in ("text", "content", "value", "answer", "question"):
            if key in value:
                return _to_text(value.get(key))
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _first_non_empty(record: dict[str, Any], aliases: Iterable[str]) -> tuple[str, str]:
    for key in aliases:
        if key not in record:
            continue
        text = _to_text(record.get(key))
        if text:
            return text, key
    return "", ""


def _first_value(record: dict[str, Any], aliases: Iterable[str]) -> tuple[Any, str]:
    for key in aliases:
        if key in record and record.get(key) is not None:
            return record[key], key
    return None, ""


def _extract_options_text(record: dict[str, Any]) -> str:
    options = record.get("options")
    if options is None:
        return ""
    if isinstance(options, dict):
        lines = [f"{k}. {_to_text(v)}" for k, v in options.items()]
        return "\n".join([x for x in lines if x.strip(". ")])
    if isinstance(options, list):
        lines = [f"{i + 1}. {_to_text(v)}" for i, v in enumerate(options)]
        return "\n".join([x for x in lines if x.strip(". ")])
    text = _to_text(options)
    return text


def _normalize_role(raw_role: str) -> str:
    role = raw_role.lower().strip()
    if role in {"human", "user", "patient", "questioner"}:
        return "user"
    if role in {"assistant", "doctor", "bot", "model"}:
        return "assistant"
    if role in {"system"}:
        return "system"
    return role or "unknown"


def _extract_conversation(record: dict[str, Any]) -> tuple[str, str, str, str]:
    messages, message_key = _first_value(record, CONVERSATION_ALIASES)
    if not isinstance(messages, list):
        return "", "", "", ""

    parsed: list[tuple[str, str]] = []
    for item in messages:
        if isinstance(item, dict):
            role_raw, _ = _first_non_empty(item, ROLE_ALIASES)
            content_raw, _ = _first_non_empty(item, CONTENT_ALIASES)
            role = _normalize_role(role_raw)
            content = content_raw.strip()
        else:
            role = "unknown"
            content = _to_text(item)
        if content:
            parsed.append((role, content))

    if not parsed:
        return "", "", "", message_key

    query_idx = -1
    answer_idx = -1
    for i, (role, _) in enumerate(parsed):
        if query_idx < 0 and role == "user":
            query_idx = i
    for i in range(len(parsed) - 1, -1, -1):
        if parsed[i][0] == "assistant":
            answer_idx = i
            break

    if query_idx < 0:
        query_idx = 0
    if answer_idx < 0:
        answer_idx = len(parsed) - 1

    query = parsed[query_idx][1]
    answer = parsed[answer_idx][1] if answer_idx != query_idx else ""

    context_lines = []
    for i, (role, content) in enumerate(parsed):
        if i in {query_idx, answer_idx}:
            continue
        context_lines.append(f"{role}: {content}")
    context = "\n".join(context_lines)
    return query, context, answer, message_key


def normalize_record(
    record: dict[str, Any],
    dataset: str,
    split: str,
    source_file: str,
    row_index: int,
) -> dict[str, Any]:
    query, query_key = _first_non_empty(record, QUERY_ALIASES)
    context, context_key = _first_non_empty(record, CONTEXT_ALIASES)
    answer, answer_key = _first_non_empty(record, ANSWER_ALIASES)

    mapped_from: dict[str, str] = {}
    if query_key:
        mapped_from["query"] = query_key
    if context_key:
        mapped_from["context"] = context_key
    if answer_key:
        mapped_from["answer"] = answer_key

    if not query or not answer:
        conv_query, conv_context, conv_answer, conv_key = _extract_conversation(record)
        if conv_key:
            if not query and conv_query:
                query = conv_query
                mapped_from["query"] = conv_key
            if not context and conv_context:
                context = conv_context
                mapped_from["context"] = conv_key
            if not answer and conv_answer:
                answer = conv_answer
                mapped_from["answer"] = conv_key

    options_text = _extract_options_text(record)
    if options_text and options_text not in query:
        query = f"{query}\n选项:\n{options_text}".strip()

    source_id, source_id_key = _first_non_empty(record, ID_ALIASES)
    if not source_id:
        source_id = f"{dataset}_{split}_{row_index:08d}"
        source_id_key = "generated"

    normalized = {
        "id": source_id,
        "query": query,
        "context": context,
        "answer": answer,
        "meta": {
            "dataset": dataset,
            "split": split,
            "source_file": source_file,
            "source_id_key": source_id_key,
            "mapped_from": mapped_from,
            "valid": bool(query and answer),
            "raw_keys": sorted(record.keys()),
        },
    }
    return normalized


def _read_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid jsonl at line {line_no}: {exc}") from exc
                if isinstance(obj, dict):
                    rows.append(obj)
        return rows

    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    if isinstance(obj, list):
        return [x for x in obj if isinstance(x, dict)]

    if isinstance(obj, dict):
        for key in ("data", "records", "items"):
            value = obj.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        merged: list[dict[str, Any]] = []
        for split_name, value in obj.items():
            if not isinstance(value, list):
                continue
            for row in value:
                if not isinstance(row, dict):
                    continue
                copied = dict(row)
                copied.setdefault("__split", split_name)
                merged.append(copied)
        if merged:
            return merged

    raise ValueError(f"Unsupported JSON structure: {path}")


def load_records(input_path: Path) -> list[dict[str, Any]]:
    suffix = input_path.suffix.lower()
    if suffix in {".jsonl", ".json"}:
        return _read_json_or_jsonl(input_path)
    if suffix == ".parquet":
        try:
            import pandas as pd  # local import to avoid hard dependency for json/jsonl use-cases
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Reading parquet requires pandas. Install with `make setup` first."
            ) from exc
        df = pd.read_parquet(input_path)
        return df.to_dict(orient="records")
    raise ValueError(f"Unsupported input extension: {input_path.suffix}")


def save_records(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".jsonl":
        with output_path.open("w", encoding="utf-8") as f:
            for row in records:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize medical QA records to unified schema.")
    parser.add_argument("--input", required=True, help="Path to raw input file (.json/.jsonl/.parquet)")
    parser.add_argument("--output", required=True, help="Path to output file (.json/.jsonl)")
    parser.add_argument("--dataset", default="unknown_dataset", help="Dataset name tag")
    parser.add_argument("--split", default="unknown_split", help="Split tag")
    parser.add_argument("--limit", type=int, default=-1, help="Max number of rows to process")
    parser.add_argument(
        "--drop-invalid",
        action="store_true",
        help="Drop rows with empty query or answer after normalization",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    records = load_records(input_path)
    if args.limit > 0:
        records = records[: args.limit]

    normalized_records = []
    valid_count = 0
    for idx, record in enumerate(records):
        split = str(record.get("__split", args.split))
        normalized = normalize_record(
            record=record,
            dataset=args.dataset,
            split=split,
            source_file=str(input_path),
            row_index=idx,
        )
        if normalized["meta"]["valid"]:
            valid_count += 1
        if args.drop_invalid and not normalized["meta"]["valid"]:
            continue
        normalized_records.append(normalized)

    save_records(normalized_records, output_path)
    print(
        f"[schema] input={len(records)} output={len(normalized_records)} "
        f"valid={valid_count} invalid={len(records) - valid_count} file={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
