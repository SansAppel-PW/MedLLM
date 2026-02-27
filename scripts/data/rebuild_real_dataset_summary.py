#!/usr/bin/env python3
"""Rebuild reports/real_dataset_summary.json from existing local data artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SOURCE_META = {
    "cmtmedqa": ("Suprit/CMtMedQA", "default", "train", "MIT"),
    "huatuo26m_lite": ("FreedomIntelligence/Huatuo26M-Lite", "default", "train", "Apache-2.0"),
    "huatuo_encyclopedia": ("FreedomIntelligence/huatuo_encyclopedia_qa", "default", "train", "Apache-2.0"),
    "medqa_usmle_train": ("GBaker/MedQA-USMLE-4-options-hf", "default", "train", "CC-BY-SA-4.0"),
}


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild real dataset summary from local files")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-json", default="reports/real_dataset_summary.json")
    parser.add_argument("--out-md", default="reports/real_dataset_report.md")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    raw_dir = root / "data/raw/real_sources"

    sources = []
    merged_before = 0
    for stem, (dataset, config, split, license_hint) in SOURCE_META.items():
        rows = count_jsonl(raw_dir / f"{stem}.jsonl")
        if rows <= 0:
            continue
        merged_before += rows
        sources.append(
            {
                "name": stem,
                "dataset": dataset,
                "config": config,
                "split": split,
                "num_rows_total": rows,
                "start_offset": 0,
                "target_count": rows,
                "fetched_count": rows,
                "license": license_hint,
            }
        )

    summary = {
        "sources": sources,
        "merged_before_dedup": merged_before,
        "merged_after_dedup": count_jsonl(raw_dir / "merged_real_qa.jsonl"),
        "train_count": count_jsonl(root / "data/clean/real_sft_train.jsonl"),
        "dev_count": count_jsonl(root / "data/clean/real_sft_dev.jsonl"),
        "test_count": count_jsonl(root / "data/clean/real_sft_test.jsonl"),
        "benchmark_count": count_jsonl(root / "data/benchmark/real_medqa_benchmark.jsonl"),
        "seed": args.seed,
        "rebuilt_from_local_artifacts": True,
    }

    out_json = (root / args.out_json).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = (root / args.out_md).resolve()
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 真实数据集构建报告",
        "",
        "## 数据源（重建）",
        "| 名称 | 数据集 | split | 采样量 | 许可 |",
        "|---|---|---|---:|---|",
    ]
    for s in sources:
        lines.append(
            f"| {s['name']} | {s['dataset']} | {s['split']} | {s['fetched_count']} | {s['license']} |"
        )
    lines.extend(
        [
            "",
            "## 合并与切分",
            f"- 合并后样本数（去重前）: {summary['merged_before_dedup']}",
            f"- 合并后样本数（去重后）: {summary['merged_after_dedup']}",
            f"- 训练集: {summary['train_count']}",
            f"- 验证集: {summary['dev_count']}",
            f"- 测试集: {summary['test_count']}",
            "",
            "## Benchmark",
            f"- real_medqa_benchmark 样本数: {summary['benchmark_count']}",
            "",
            "注：该报告由已有本地产物重建，用于迁移同步后恢复 summary 口径。",
        ]
    )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"summary_json": str(out_json), "sources": len(sources)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
