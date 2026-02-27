#!/usr/bin/env python3
"""Build a reference KB from labeled benchmark positives.

The generated KB is used by retrieval/NLI modules for offline, same-benchmark
consistency checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

RELATION_TEXT = {
    "treats": "可用于治疗",
    "contraindicated_for": "禁用于",
    "dosage_range_mg": "推荐剂量范围",
    "dosage": "用量",
    "reference_answer": "参考答案",
}


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


def pair_key(sample_id: str) -> str:
    sid = (sample_id or "").strip()
    sid = re.sub(r"_(pos|neg)$", "", sid)
    return sid


def canonical_answer_text(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"(?:正确答案|correct answer)\s*[:：]?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^[A-D](?:[.\)\s]+)", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_split_spec(spec: str) -> set[str]:
    items = [x.strip().lower() for x in (spec or "").split(",") if x.strip()]
    return set(items)


def split_of(row: dict[str, Any]) -> str:
    meta = row.get("meta", {})
    if not isinstance(meta, dict):
        return ""
    return str(meta.get("split", "")).strip().lower()


def build_reference_rows(
    benchmark_rows: list[dict[str, Any]],
    include_splits: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    filtered_rows = benchmark_rows
    if include_splits:
        filtered_rows = [row for row in benchmark_rows if split_of(row) in include_splits]

    by_key: dict[str, dict[str, Any]] = {}
    for row in filtered_rows:
        rid = str(row.get("id", ""))
        key = pair_key(rid)
        expected = str(row.get("expected_risk", "low"))
        query = str(row.get("query", "")).strip()
        answer = str(row.get("answer", "")).strip()
        if not query or not answer:
            continue
        slot = by_key.setdefault(key, {"query": query, "positive": None, "negative": None})
        slot["query"] = query
        if expected == "low" or rid.endswith("_pos"):
            slot["positive"] = answer
        else:
            slot["negative"] = answer

    out_rows: list[dict[str, Any]] = []
    seen_query_hash = set()
    missing_positive = 0
    for key, info in by_key.items():
        query = str(info.get("query", "")).strip()
        positive = str(info.get("positive") or "").strip()
        if not positive:
            missing_positive += 1
            continue
        q_hash = hashlib.md5(query.strip().lower().encode("utf-8")).hexdigest()
        if q_hash in seen_query_hash:
            continue
        seen_query_hash.add(q_hash)

        answer_body = canonical_answer_text(positive)
        text = (
            "Question:\n"
            f"{query}\n\n"
            "Correct answer:\n"
            f"{positive}\n"
        )
        out_rows.append(
            {
                "id": f"ref_{len(out_rows):06d}",
                "head": query,
                "relation": "reference_answer",
                "tail": answer_body or positive,
                "query_hash": q_hash,
                "text": text,
                "meta": {
                    "pair_key": key,
                },
            }
        )

    summary = {
        "benchmark_rows": len(benchmark_rows),
        "benchmark_rows_after_split_filter": len(filtered_rows),
        "pair_count": len(by_key),
        "kb_rows": len(out_rows),
        "missing_positive_pairs": missing_positive,
        "include_splits": sorted(include_splits) if include_splits else [],
    }
    return out_rows, summary


def row_identity(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("head", "")).strip(),
        str(row.get("relation", "")).strip(),
        str(row.get("tail", "")).strip(),
        str(row.get("text", "")).strip(),
    )


def merge_extra_kb(
    base_rows: list[dict[str, Any]],
    extra_rows: list[dict[str, Any]],
    extra_max: int,
) -> dict[str, Any]:
    source_rows = extra_rows[:extra_max] if extra_max > 0 else extra_rows
    seen = {row_identity(r) for r in base_rows}
    added = 0

    for i, row in enumerate(source_rows):
        head = str(row.get("head", "")).strip()
        relation = str(row.get("relation", "")).strip()
        tail = str(row.get("tail", "")).strip()
        if not head and not tail:
            continue

        if row.get("text"):
            text = str(row.get("text", "")).strip()
        else:
            rel_text = RELATION_TEXT.get(relation, relation or "related_to")
            text = f"{head}{rel_text}{tail}".strip()

        merged = {
            "id": f"extra_{i:06d}",
            "head": head,
            "relation": relation or "related_to",
            "tail": tail,
            "query_hash": "",
            "text": text,
            "meta": {
                "pair_key": "",
                "source_dataset": str(row.get("source", "") or "extra_kg"),
            },
        }
        key = row_identity(merged)
        if key in seen:
            continue
        seen.add(key)
        base_rows.append(merged)
        added += 1

    return {
        "extra_rows_input": len(extra_rows),
        "extra_rows_considered": len(source_rows),
        "extra_rows_added": added,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build benchmark reference KB")
    parser.add_argument("--benchmark", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--output", default="data/kg/real_medqa_reference_kb.jsonl")
    parser.add_argument("--report", default="reports/benchmark_reference_kb_report.md")
    parser.add_argument("--extra-kg", default="", help="Optional external KG jsonl (e.g., cmekg_integrated)")
    parser.add_argument("--extra-kg-max", type=int, default=12000, help="Max external KG rows to merge")
    parser.add_argument(
        "--include-splits",
        default="train",
        help="Comma-separated benchmark splits used to build KB (e.g. train)",
    )
    args = parser.parse_args()

    benchmark_path = Path(args.benchmark)
    rows = load_jsonl(benchmark_path)
    include_splits = parse_split_spec(args.include_splits)
    kb_rows, summary = build_reference_rows(rows, include_splits=include_splits)

    extra_summary = {
        "extra_rows_input": 0,
        "extra_rows_considered": 0,
        "extra_rows_added": 0,
        "extra_kg_path": args.extra_kg,
        "extra_kg_exists": False,
    }
    if args.extra_kg:
        extra_path = Path(args.extra_kg)
        if extra_path.exists():
            extra_rows = load_jsonl(extra_path)
            extra_summary["extra_kg_exists"] = True
            extra_summary.update(merge_extra_kb(kb_rows, extra_rows, args.extra_kg_max))

    summary["kb_rows_after_merge"] = len(kb_rows)
    save_jsonl(Path(args.output), kb_rows)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# Benchmark 参考知识库构建报告",
        "",
        f"- 基准集样本数: {summary['benchmark_rows']}",
        f"- split 过滤后样本数: {summary['benchmark_rows_after_split_filter']}",
        f"- 使用 split: {','.join(summary['include_splits']) if summary['include_splits'] else '(all)'}",
        f"- 问题对数量: {summary['pair_count']}",
        f"- 参考知识条目数(基础): {summary['kb_rows']}",
        f"- 参考知识条目数(合并后): {summary['kb_rows_after_merge']}",
        f"- 缺少正例的问题对: {summary['missing_positive_pairs']}",
        f"- 额外KG路径: `{args.extra_kg or '(none)'}`",
        f"- 额外KG是否存在: {extra_summary['extra_kg_exists']}",
        f"- 额外KG输入条目: {extra_summary['extra_rows_input']}",
        f"- 额外KG并入条目: {extra_summary['extra_rows_added']}",
        "",
        f"- 输出: `{args.output}`",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps({**summary, **extra_summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
