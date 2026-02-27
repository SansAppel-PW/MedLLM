#!/usr/bin/env python3
"""Build unified thesis real assets from CM3KG + external QA sources.

This script merges:
- CM3KG-derived SFT splits
- Real QA corpus (Huatuo/CMtMedQA merged jsonl)
- Benchmark pairs from MedQA and CM3KG

Outputs:
- data/clean/real_sft_{train,dev,test}.jsonl
- data/benchmark/real_medqa_benchmark.jsonl (combined benchmark)
- reports/real_dataset_summary.json
- reports/real_dataset_report.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stable_key(row: dict[str, Any]) -> str:
    query = str(row.get("query", "") or "").strip()
    answer = str(row.get("answer", "") or "").strip()
    return hashlib.md5(f"{query}\n{answer}".encode("utf-8")).hexdigest()


def deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = set()
    for row in rows:
        key = stable_key(row)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def split_rows(rows: list[dict[str, Any]], seed: int, dev_ratio: float, test_ratio: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not rows:
        return [], [], []
    rng = random.Random(seed)
    data = rows[:]
    rng.shuffle(data)
    n = len(data)
    n_dev = max(1, int(n * dev_ratio))
    n_test = max(1, int(n * test_ratio))
    if n_dev + n_test >= n:
        n_dev = max(1, n // 10)
        n_test = max(1, n // 10)
    if n_dev + n_test >= n:
        n_dev, n_test = 1, 1
    n_train = max(1, n - n_dev - n_test)
    n_dev = min(n_dev, n - n_train - 1)
    n_test = n - n_train - n_dev
    return data[:n_train], data[n_train : n_train + n_dev], data[n_train + n_dev :]


def ensure_split_tag(rows: list[dict[str, Any]], split: str, source_group: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        obj = dict(row)
        meta = obj.get("meta")
        if not isinstance(meta, dict):
            meta = {}
        else:
            meta = dict(meta)
        meta["split"] = split
        meta["source_group"] = source_group
        obj["meta"] = meta
        out.append(obj)
    return out


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build unified thesis real assets")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-raw-rows", type=int, default=0, help="0 means use all rows")
    parser.add_argument("--dev-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)

    parser.add_argument("--cm3kg-train", default="data/clean/cm3kg_sft_train.jsonl")
    parser.add_argument("--cm3kg-dev", default="data/clean/cm3kg_sft_dev.jsonl")
    parser.add_argument("--cm3kg-test", default="data/clean/cm3kg_sft_test.jsonl")
    parser.add_argument("--raw-merged", default="data/raw/real_sources/merged_real_qa.jsonl")
    parser.add_argument("--medqa-benchmark", default="data/benchmark/real_medqa_benchmark_from_hf.jsonl")
    parser.add_argument("--cm3kg-benchmark", default="data/benchmark/cm3kg_benchmark.jsonl")

    parser.add_argument("--out-train", default="data/clean/real_sft_train.jsonl")
    parser.add_argument("--out-dev", default="data/clean/real_sft_dev.jsonl")
    parser.add_argument("--out-test", default="data/clean/real_sft_test.jsonl")
    parser.add_argument("--out-benchmark", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--summary-out", default="reports/real_dataset_summary.json")
    parser.add_argument("--report-out", default="reports/real_dataset_report.md")

    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]

    cm3kg_train = ensure_split_tag(load_jsonl(root / args.cm3kg_train), "train", "cm3kg")
    cm3kg_dev = ensure_split_tag(load_jsonl(root / args.cm3kg_dev), "validation", "cm3kg")
    cm3kg_test = ensure_split_tag(load_jsonl(root / args.cm3kg_test), "test", "cm3kg")

    raw_rows = deduplicate(load_jsonl(root / args.raw_merged))
    rng = random.Random(args.seed + 11)
    if args.max_raw_rows > 0 and len(raw_rows) > args.max_raw_rows:
        rng.shuffle(raw_rows)
        raw_rows = raw_rows[: args.max_raw_rows]
    raw_train, raw_dev, raw_test = split_rows(raw_rows, args.seed, args.dev_ratio, args.test_ratio)
    raw_train = ensure_split_tag(raw_train, "train", "external_real_qa")
    raw_dev = ensure_split_tag(raw_dev, "validation", "external_real_qa")
    raw_test = ensure_split_tag(raw_test, "test", "external_real_qa")

    final_train = deduplicate(cm3kg_train + raw_train)
    final_dev = deduplicate(cm3kg_dev + raw_dev)
    final_test = deduplicate(cm3kg_test + raw_test)
    rng.shuffle(final_train)
    rng.shuffle(final_dev)
    rng.shuffle(final_test)

    write_jsonl(root / args.out_train, final_train)
    write_jsonl(root / args.out_dev, final_dev)
    write_jsonl(root / args.out_test, final_test)

    medqa_benchmark = load_jsonl(root / args.medqa_benchmark)
    cm3kg_benchmark = load_jsonl(root / args.cm3kg_benchmark)
    benchmark_rows = deduplicate(medqa_benchmark + cm3kg_benchmark)
    if not benchmark_rows:
        raise RuntimeError("Benchmark rows are empty after merge. At least one benchmark source is required.")
    write_jsonl(root / args.out_benchmark, benchmark_rows)

    raw_sources_dir = root / "data/raw/real_sources"
    raw_stats = {
        "cmtmedqa_count": count_lines(raw_sources_dir / "cmtmedqa.jsonl"),
        "huatuo26m_lite_count": count_lines(raw_sources_dir / "huatuo26m_lite.jsonl"),
        "huatuo_encyclopedia_count": count_lines(raw_sources_dir / "huatuo_encyclopedia.jsonl"),
        "merged_real_qa_count": count_lines(raw_sources_dir / "merged_real_qa.jsonl"),
    }

    summary = {
        "source_requirements": {
            "proposal_required_sources": [
                "CMeKG/CM3KG",
                "Huatuo-26M",
                "MedQA",
                "CMtMedQA",
            ],
            "cm3kg_used": bool(cm3kg_train or cm3kg_dev or cm3kg_test),
            "external_real_qa_used": bool(raw_rows),
            "medqa_benchmark_used": bool(medqa_benchmark),
        },
        "cm3kg_component": {
            "train_count": len(cm3kg_train),
            "dev_count": len(cm3kg_dev),
            "test_count": len(cm3kg_test),
            "benchmark_count": len(cm3kg_benchmark),
        },
        "external_real_qa_component": {
            "raw_merged_count": len(raw_rows),
            "train_count": len(raw_train),
            "dev_count": len(raw_dev),
            "test_count": len(raw_test),
            "source_file_counts": raw_stats,
        },
        "final_sft": {
            "train_count": len(final_train),
            "dev_count": len(final_dev),
            "test_count": len(final_test),
        },
        "final_benchmark": {
            "count": len(benchmark_rows),
            "medqa_component_count": len(medqa_benchmark),
            "cm3kg_component_count": len(cm3kg_benchmark),
        },
        "seed": args.seed,
        "artifacts": {
            "train_file": args.out_train,
            "dev_file": args.out_dev,
            "test_file": args.out_test,
            "benchmark_file": args.out_benchmark,
        },
    }

    summary_path = root / args.summary_out
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 真实数据集构建报告（统一版）",
        "",
        "## 来源覆盖",
        "- CMeKG/CM3KG: 已接入（用于 KG 与结构化医学事实样本）",
        "- Huatuo-26M/CMtMedQA: 已接入（用于真实医疗问答 SFT）",
        "- MedQA: 已接入（用于 benchmark 与事实核验评测）",
        "",
        "## 组成规模",
        f"- CM3KG 组件（train/dev/test）: {len(cm3kg_train)}/{len(cm3kg_dev)}/{len(cm3kg_test)}",
        f"- 外部问答组件（train/dev/test）: {len(raw_train)}/{len(raw_dev)}/{len(raw_test)}",
        f"- 最终训练集（train/dev/test）: {len(final_train)}/{len(final_dev)}/{len(final_test)}",
        "",
        "## Benchmark",
        f"- MedQA benchmark 条目: {len(medqa_benchmark)}",
        f"- CM3KG benchmark 条目: {len(cm3kg_benchmark)}",
        f"- 合并 benchmark 条目: {len(benchmark_rows)}",
        "",
        "## 原始文件规模（data/raw/real_sources）",
        f"- cmtmedqa.jsonl: {raw_stats['cmtmedqa_count']}",
        f"- huatuo26m_lite.jsonl: {raw_stats['huatuo26m_lite_count']}",
        f"- huatuo_encyclopedia.jsonl: {raw_stats['huatuo_encyclopedia_count']}",
        f"- merged_real_qa.jsonl: {raw_stats['merged_real_qa_count']}",
    ]
    report_path = root / args.report_out
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

