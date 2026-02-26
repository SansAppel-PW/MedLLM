#!/usr/bin/env python3
"""Generate thesis-draft support material from experiment artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any


TABLE_LINE_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def parse_eval_table(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in load_lines(path):
        m = TABLE_LINE_RE.match(line.strip())
        if not m:
            continue
        model = m.group(1).strip()
        if model in {"模型", "---"}:
            continue
        rows.append(
            {
                "model": model,
                "factscore": m.group(2).strip(),
                "utility": m.group(3).strip(),
                "risk_score": m.group(4).strip(),
                "interception_rate": m.group(5).strip(),
            }
        )
    return rows


def git_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def format_training_status(metric: dict[str, Any]) -> str:
    if not metric:
        return "缺失"
    if bool(metric.get("skipped", False)):
        return f"skipped ({metric.get('skip_reason', 'unknown')})"
    if bool(metric.get("simulation", False)):
        return "proxy/simulation"
    return "real"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate thesis draft support material")
    parser.add_argument("--dataset-summary", default="reports/real_dataset_summary.json")
    parser.add_argument("--sft", default="reports/training/layer_b_qwen25_7b_sft_metrics.json")
    parser.add_argument("--dpo", default="reports/training/dpo_metrics.json")
    parser.add_argument("--simpo", default="reports/training/simpo_metrics.json")
    parser.add_argument("--kto", default="reports/training/kto_metrics.json")
    parser.add_argument("--eval-default", default="reports/eval_default.md")
    parser.add_argument("--sota-csv", default="reports/thesis_assets/tables/sota_compare_metrics.csv")
    parser.add_argument("--error-analysis", default="reports/error_analysis.md")
    parser.add_argument("--resource", default="reports/training/resource_preflight.json")
    parser.add_argument("--skip-report", default="reports/training/resource_skip_report.md")
    parser.add_argument("--output-md", default="reports/thesis_support/thesis_draft_material.md")
    parser.add_argument("--output-json", default="reports/thesis_support/experiment_record.json")
    args = parser.parse_args()

    dataset = load_json(Path(args.dataset_summary))
    sft = load_json(Path(args.sft))
    dpo = load_json(Path(args.dpo))
    simpo = load_json(Path(args.simpo))
    kto = load_json(Path(args.kto))
    resource = load_json(Path(args.resource))
    eval_rows = parse_eval_table(Path(args.eval_default))
    sota_rows = load_csv(Path(args.sota_csv))

    error_lines = load_lines(Path(args.error_analysis))
    error_summary = [x for x in error_lines if x.startswith("- ")]

    out_md = Path(args.output_md)
    out_json = Path(args.output_json)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    training_status = {
        "sft": format_training_status(sft),
        "dpo": format_training_status(dpo),
        "simpo": format_training_status(simpo),
        "kto": format_training_status(kto),
    }

    lines = [
        "# 论文初稿支撑材料（自动生成）",
        "",
        f"- 生成时间（UTC）: {dataset.get('generated_at_utc', 'N/A')}",
        f"- 代码版本: `{git_commit()}`",
        "",
        "## 1. 研究目标与创新点映射",
        "- 目标一：以 KG 数据治理降低训练数据事实噪声。",
        "- 目标二：以白盒不确定性 + 黑盒检索核查构建混合幻觉检测。",
        "- 目标三：以 DPO/SimPO/KTO 偏好对齐抑制高风险医疗幻觉。",
        "",
        "## 2. 数据与实验设置记录",
        f"- merged_after_dedup: {dataset.get('merged_after_dedup', 'N/A')}",
        f"- train/dev/test: {dataset.get('train_count', 'N/A')} / {dataset.get('dev_count', 'N/A')} / {dataset.get('test_count', 'N/A')}",
        f"- benchmark_count: {dataset.get('benchmark_count', 'N/A')}",
        f"- seed: {dataset.get('seed', 'N/A')}",
        "",
        "## 3. 训练执行状态",
        f"- SFT: {training_status['sft']}",
        f"- DPO: {training_status['dpo']}",
        f"- SimPO: {training_status['simpo']}",
        f"- KTO: {training_status['kto']}",
        f"- 资源探测: accelerator={resource.get('accelerator', 'N/A')}, cuda_total_mem_gb={resource.get('cuda_total_mem_gb', 'N/A')}",
        f"- 跳过报告: `{args.skip_report}`",
        "",
        "## 4. 综合评测主结果",
        "| model | factscore | utility | risk_score | interception_rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in eval_rows:
        lines.append(
            f"| {row['model']} | {row['factscore']} | {row['utility']} | {row['risk_score']} | {row['interception_rate']} |"
        )

    lines.extend(
        [
            "",
            "## 5. 对标实验主结果（节选）",
            "| name | accuracy | recall | specificity | unsafe_pass_rate | f1 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in sota_rows[:4]:
        lines.append(
            f"| {row.get('name','')} | {row.get('accuracy','')} | {row.get('recall','')} | "
            f"{row.get('specificity','')} | {row.get('unsafe_pass_rate','')} | {row.get('f1','')} |"
        )

    lines.extend(
        [
            "",
            "## 6. 错误分析要点",
            *error_summary[:8],
            "",
            "## 7. 论文撰写建议（可直接展开为章节）",
            "1. 数据治理章节：阐述 CMeKG 校验与冲突样本处理流程。",
            "2. 检测章节：解释混合检测为何提升 recall 并分析 specificity 风险。",
            "3. 对齐章节：说明真实训练与资源受限跳过策略的证据边界。",
            "4. 讨论章节：结合 Top 错误案例给出可执行改进方向。",
        ]
    )

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    out_payload = {
        "git_commit": git_commit(),
        "dataset": dataset,
        "training_status": training_status,
        "resource": resource,
        "eval_rows": eval_rows,
        "sota_top4": sota_rows[:4],
        "error_summary": error_summary[:8],
    }
    out_json.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {"output_md": str(out_md), "output_json": str(out_json), "eval_rows": len(eval_rows)},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
