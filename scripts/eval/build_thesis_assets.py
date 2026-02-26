#!/usr/bin/env python3
"""Assemble thesis-ready tables/figures from experiment artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


POSITIVE_LEVELS = {"high", "medium"}


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def confusion_from_predictions(rows: list[dict[str, Any]]) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for row in rows:
        gold = str(row.get("expected_risk", "low")) in POSITIVE_LEVELS
        pred = str(row.get("predicted_risk", "low")) in POSITIVE_LEVELS
        if gold and pred:
            tp += 1
        elif (not gold) and pred:
            fp += 1
        elif (not gold) and (not pred):
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build thesis assets")
    parser.add_argument("--out-dir", default="reports/thesis_assets")
    parser.add_argument("--dataset-summary", default="reports/real_dataset_summary.json")
    parser.add_argument("--dpo", default="reports/training/dpo_metrics.json")
    parser.add_argument("--simpo", default="reports/training/simpo_metrics.json")
    parser.add_argument("--kto", default="reports/training/kto_metrics.json")
    parser.add_argument("--predictions", default="reports/detection_predictions.jsonl")
    parser.add_argument("--sota-csv", default="reports/thesis_assets/tables/sota_compare_metrics.csv")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    tables_dir = out_dir / "tables"
    figures_dir = out_dir / "figures"
    cases_dir = out_dir / "cases"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    cases_dir.mkdir(parents=True, exist_ok=True)

    dataset_summary = load_json(Path(args.dataset_summary)) or {}
    dpo = load_json(Path(args.dpo)) or {}
    simpo = load_json(Path(args.simpo)) or {}
    kto = load_json(Path(args.kto)) or {}
    predictions = load_jsonl(Path(args.predictions))
    confusion = confusion_from_predictions(predictions)

    experiment_rows = [
        {
            "section": "real_dataset",
            "metric": "merged_after_dedup",
            "value": dataset_summary.get("merged_after_dedup", 0),
        },
        {
            "section": "real_dataset",
            "metric": "train_count",
            "value": dataset_summary.get("train_count", 0),
        },
        {
            "section": "real_dataset",
            "metric": "dev_count",
            "value": dataset_summary.get("dev_count", 0),
        },
        {
            "section": "real_dataset",
            "metric": "test_count",
            "value": dataset_summary.get("test_count", 0),
        },
        {
            "section": "real_dataset",
            "metric": "benchmark_count",
            "value": dataset_summary.get("benchmark_count", 0),
        },
        {
            "section": "alignment",
            "metric": "dpo_aligned_score",
            "value": dpo.get("aligned_score", 0),
        },
        {
            "section": "alignment",
            "metric": "simpo_aligned_score",
            "value": simpo.get("aligned_score", 0),
        },
        {
            "section": "alignment",
            "metric": "kto_aligned_score",
            "value": kto.get("aligned_score", 0),
        },
    ]
    write_csv(
        tables_dir / "experiment_overview.csv",
        ["section", "metric", "value"],
        experiment_rows,
    )

    confusion_rows = [
        {"name": "TP", "count": confusion["tp"]},
        {"name": "FP", "count": confusion["fp"]},
        {"name": "TN", "count": confusion["tn"]},
        {"name": "FN", "count": confusion["fn"]},
    ]
    write_csv(tables_dir / "detection_confusion.csv", ["name", "count"], confusion_rows)

    flow_figure = [
        "# Figure: Pipeline Flow (Mermaid)",
        "",
        "```mermaid",
        "flowchart LR",
        '  A["真实数据抓取"] --> B["Schema与清洗"]',
        '  B --> C["偏好对构建"]',
        '  C --> D["SFT / DPO / SimPO"]',
        '  B --> E["参考KB构建"]',
        '  E --> F["白盒+检索混合检测"]',
        '  D --> G["服务层与Demo"]',
        '  F --> G',
        '  G --> H["评测与论文资产"]',
        "```",
    ]
    (figures_dir / "pipeline_mermaid.md").write_text("\n".join(flow_figure) + "\n", encoding="utf-8")

    result_notes = [
        "# Figure Notes",
        "",
        "- 可将 `tables/experiment_overview.csv` 导入论文图表工具生成总体实验表。",
        "- 可将 `tables/detection_confusion.csv` 绘制为混淆矩阵柱状图。",
        "- 可将 `tables/sota_compare_metrics.csv` 绘制为系统对比雷达图或条形图。",
    ]
    (figures_dir / "result_figure_notes.md").write_text("\n".join(result_notes) + "\n", encoding="utf-8")

    readme_lines = [
        "# Thesis Assets",
        "",
        "本目录用于论文写作时直接引用。",
        "",
        "## 结构",
        "- `tables/experiment_overview.csv`: 数据规模与训练结果总览",
        "- `tables/detection_confusion.csv`: 检测混淆矩阵",
        "- `tables/sota_compare_metrics.csv`: 对标实验指标（由 `run_sota_compare.py` 生成）",
        "- `tables/training_loss_summary.csv`: 训练曲线统计摘要（由 `build_training_figures.py` 生成）",
        "- `cases/error_cases_top30.jsonl`: 错误案例样本（由 `generate_error_analysis.py` 生成）",
        "- `figures/pipeline_mermaid.md`: 流程图源码",
        "- `figures/result_figure_notes.md`: 图表建议",
        "",
        "## 论文初稿材料",
        "- `../thesis_support/thesis_draft_material.md`: 论文正文支撑草稿",
        "- `../thesis_support/thesis_readiness.md`: 六项交付完备度检查",
    ]
    (out_dir / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "out_dir": str(out_dir),
                "predictions": len(predictions),
                "overview_rows": len(experiment_rows),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
