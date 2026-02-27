#!/usr/bin/env python3
"""Audit project alignment against opening proposal requirements."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    section: str
    item: str
    status: str  # PASS | WARN | FAIL
    evidence: str
    action: str


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_exists(results: list[CheckResult], section: str, item: str, path: Path, action: str) -> None:
    if path.exists():
        results.append(
            CheckResult(section, item, "PASS", f"存在: `{path}`", action)
        )
    else:
        results.append(
            CheckResult(section, item, "FAIL", f"缺失: `{path}`", action)
        )


def has_dataset(summary: dict[str, Any], dataset_name: str) -> bool:
    sources = summary.get("sources", [])
    for row in sources:
        if str(row.get("dataset", "")).strip() == dataset_name:
            return True
    return False


def check_metric_real(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "FAIL", f"缺失: `{path}`"
    payload = load_json(path)
    if not payload:
        return "WARN", f"无法解析: `{path}`"
    if payload.get("simulation") is False:
        return "PASS", f"真实训练指标: `{path}`"
    if payload.get("skipped") is True or payload.get("simulation") is True:
        return "WARN", f"仍为降级/模拟: `{path}`"
    # SFT 指标没有 simulation 字段时，只要存在 loss 即判定可用
    if "train_loss" in payload:
        return "PASS", f"存在 train_loss: `{path}`"
    return "WARN", f"指标口径不明确: `{path}`"


def build_report(results: list[CheckResult]) -> tuple[str, dict[str, int]]:
    stat = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for row in results:
        stat[row.status] += 1

    lines = [
        "# 开题要求一致性审计报告",
        "",
        "| 模块 | 检查项 | 状态 | 证据 | 修复/动作 |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row.section} | {row.item} | {row.status} | {row.evidence} | {row.action} |"
        )

    lines.extend(
        [
            "",
            "## 汇总",
            f"- PASS: {stat['PASS']}",
            f"- WARN: {stat['WARN']}",
            f"- FAIL: {stat['FAIL']}",
            "",
            "## 结论",
            "- 若 FAIL=0 且关键训练指标为真实口径，则可进入论文写作主线。",
            "- 若存在 WARN，需在论文中如实标注限制条件与后续补实验计划。",
        ]
    )
    return "\n".join(lines) + "\n", stat


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit proposal alignment")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-md", default="reports/audit_opening_alignment.md")
    parser.add_argument("--output-json", default="reports/audit_opening_alignment.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results: list[CheckResult] = []

    # 1) 数据源一致性
    dataset_summary = load_json(root / "reports/real_dataset_summary.json")
    if dataset_summary:
        checks = [
            ("Suprit/CMtMedQA", "CMtMedQA 数据源"),
            ("FreedomIntelligence/Huatuo26M-Lite", "Huatuo-26M-Lite 数据源"),
        ]
        for dataset_name, item in checks:
            ok = has_dataset(dataset_summary, dataset_name)
            if ok:
                results.append(
                    CheckResult("数据源", item, "PASS", f"reports/real_dataset_summary.json 包含 `{dataset_name}`", "保持")
                )
            else:
                results.append(
                    CheckResult("数据源", item, "WARN", f"summary 未发现 `{dataset_name}`", "重跑 build_real_dataset.py 并启用对应 source")
                )

        medqa_ok = has_dataset(dataset_summary, "GBaker/MedQA-USMLE-4-options-hf")
        medqa_benchmark = root / "data/benchmark/real_medqa_benchmark.jsonl"
        if medqa_ok:
            results.append(
                CheckResult("数据源", "MedQA 数据源", "PASS", "summary 包含 `GBaker/MedQA-USMLE-4-options-hf`", "保持")
            )
        elif medqa_benchmark.exists():
            results.append(
                CheckResult(
                    "数据源",
                    "MedQA 数据源",
                    "PASS",
                    "benchmark 文件存在并由 MedQA 构建: `data/benchmark/real_medqa_benchmark.jsonl`",
                    "如需将 MedQA 纳入 SFT，重跑 build_real_dataset.py --medqa-count",
                )
            )
        else:
            results.append(
                CheckResult(
                    "数据源",
                    "MedQA 数据源",
                    "WARN",
                    "summary 与 benchmark 均未发现 MedQA 证据",
                    "重跑 build_real_dataset.py 并检查 MedQA 取数链路",
                )
            )
    else:
        results.append(
            CheckResult("数据源", "real_dataset_summary", "FAIL", "缺失 reports/real_dataset_summary.json", "先执行真实数据构建")
        )

    check_exists(
        results,
        "数据源",
        "CM3KG 本地知识图谱目录",
        root / "CM3KG",
        "保持或迁移到 GPU 环境后同路径挂载",
    )
    check_exists(
        results,
        "知识图谱",
        "集成 CMeKG 文件",
        root / "data/kg/cmekg_integrated.jsonl",
        "执行 scripts/data/build_cmekg_from_cm3kg.py",
    )

    # 2) RAG + 检测链路
    check_exists(results, "检测/RAG", "原子事实抽取", root / "src/detect/atomic_fact_extractor.py", "保持")
    check_exists(results, "检测/RAG", "检索模块", root / "src/detect/retriever.py", "保持")
    check_exists(results, "检测/RAG", "NLI核查", root / "src/detect/nli_checker.py", "保持")
    check_exists(results, "检测/RAG", "运行时守卫", root / "src/detect/runtime_guard.py", "保持")

    # 3) 训练闭环
    check_exists(results, "训练", "真实 SFT 入口", root / "src/train/real_sft_train.py", "保持")
    check_exists(results, "训练", "真实偏好对齐入口", root / "src/train/real_pref_train.py", "保持")
    check_exists(results, "训练", "对齐编排脚本", root / "scripts/train/run_real_alignment_pipeline.sh", "保持")

    metric_targets = [
        ("SFT 指标", root / "reports/training/layer_b_qwen25_7b_sft_metrics.json"),
        ("DPO 指标", root / "reports/training/dpo_metrics.json"),
        ("SimPO 指标", root / "reports/training/simpo_metrics.json"),
        ("KTO 指标", root / "reports/training/kto_metrics.json"),
    ]
    for item, path in metric_targets:
        status, evidence = check_metric_real(path)
        action = "指标已可用于论文" if status == "PASS" else "需在 GPU 上重跑真实训练并同步报告"
        results.append(CheckResult("训练", item, status, evidence, action))

    # 4) 论文链路
    check_exists(results, "论文产物", "数据报告", root / "reports/real_dataset_report.md", "保持")
    check_exists(results, "论文产物", "清洗报告", root / "reports/data_cleaning_report.md", "保持")
    check_exists(results, "论文产物", "综合评测", root / "reports/eval_default.md", "保持")
    check_exists(results, "论文产物", "SOTA 对比", root / "reports/sota_compare.md", "保持")
    check_exists(results, "论文产物", "论文草稿材料", root / "reports/thesis_support/thesis_draft_material.md", "保持")

    report_text, stat = build_report(results)
    output_md = (root / args.output_md).resolve()
    output_json = (root / args.output_json).resolve()
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(report_text, encoding="utf-8")
    output_json.write_text(
        json.dumps(
            {
                "summary": stat,
                "results": [row.__dict__ for row in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps({"summary": stat, "report": str(output_md)}, ensure_ascii=False))
    return 0 if stat["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
