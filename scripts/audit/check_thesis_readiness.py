#!/usr/bin/env python3
"""Check thesis deliverable readiness against required evidence chain."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def exists(path: str) -> bool:
    return Path(path).exists()


def load_json(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_rows(path: str) -> list[dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _training_mode(metrics: dict[str, Any]) -> str:
    if not metrics:
        return "missing"
    if bool(metrics.get("skipped", False)):
        return "skipped"
    if bool(metrics.get("simulation", False)):
        return "simulation"
    return "real"


def load_checkpoint_evidence(path: str) -> dict[str, dict[str, Any]]:
    payload = load_json(path)
    comps = payload.get("components", {}) if isinstance(payload, dict) else {}
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(comps, dict):
        return out
    for name, item in comps.items():
        if isinstance(item, dict):
            out[str(name)] = item
    return out


def status_for_training_bundle(skip_path: str, checkpoint_evidence_path: str) -> tuple[str, str]:
    specs = [
        (
            "SFT",
            "reports/training/layer_b_qwen25_7b_sft_metrics.json",
            "checkpoints/layer_b/qwen25_7b_sft/final",
        ),
        ("DPO", "reports/training/dpo_metrics.json", "checkpoints/dpo-real-baseline/final"),
        ("SimPO", "reports/training/simpo_metrics.json", "checkpoints/simpo-real-baseline/final"),
        ("KTO", "reports/training/kto_metrics.json", "checkpoints/kto-real-baseline/final"),
    ]

    mode_by_name: list[tuple[str, str]] = []
    missing_metrics: list[str] = []
    missing_ckpt: list[str] = []
    ckpt_evidence_used: list[str] = []
    checkpoint_evidence = load_checkpoint_evidence(checkpoint_evidence_path)

    for name, metrics_path, ckpt_path in specs:
        metrics = load_json(metrics_path)
        mode = _training_mode(metrics)
        mode_by_name.append((name, mode))
        if mode == "missing":
            missing_metrics.append(metrics_path)
        if mode == "real" and not exists(ckpt_path):
            evidence = checkpoint_evidence.get(name, {})
            if bool(evidence.get("verified", False)):
                ckpt_evidence_used.append(name)
            else:
                missing_ckpt.append(ckpt_path)

    status_pairs = ", ".join(f"{name}:{mode}" for name, mode in mode_by_name)
    skip_evidence = exists(skip_path)

    if missing_metrics:
        if skip_evidence:
            return "DEFERRED", f"训练未完整产出，已记录跳过证据（{skip_path}）；状态={status_pairs}"
        return "FAIL", f"缺失训练指标：{'; '.join(missing_metrics)}；状态={status_pairs}"

    if any(mode in {"skipped", "simulation"} for _, mode in mode_by_name):
        if skip_evidence:
            return "DEFERRED", f"训练包含 skipped/simulation，已记录跳过证据（{skip_path}）；状态={status_pairs}"
        return "FAIL", f"训练非真实闭环且无跳过证据；状态={status_pairs}"

    if missing_ckpt:
        return "FAIL", f"训练指标为 real，但缺失 checkpoint：{'; '.join(missing_ckpt)}"

    if ckpt_evidence_used:
        used = ",".join(ckpt_evidence_used)
        return "PASS", f"真实训练闭环完整；部分 checkpoint 通过证据清单验证（{checkpoint_evidence_path}，组件={used}）；状态={status_pairs}"

    return "PASS", f"真实训练闭环完整；状态={status_pairs}"


def has_real_sft_loss_curve() -> bool:
    # Direct figure paths (naming differs across historical script versions)
    direct_candidates = [
        "reports/thesis_assets/figures/training_loss_qwen25_7b_sft.png",
        "reports/thesis_assets/figures/training_loss_layer_b_qwen25_7b_sft.png",
    ]
    if any(exists(p) for p in direct_candidates):
        return True

    # Fallback: validate from summary CSV when figure name differs.
    rows = load_csv_rows("reports/thesis_assets/tables/training_loss_summary.csv")
    for row in rows:
        source_log = str(row.get("source_log", ""))
        if source_log != "logs/layer_b/qwen25_7b_sft/train_log.jsonl":
            continue
        try:
            points = int(float(str(row.get("points", "0"))))
        except ValueError:
            points = 0
        figure_path = str(row.get("figure", "")).strip()
        if points > 0 and figure_path and exists(figure_path):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check thesis readiness")
    parser.add_argument("--report", default="reports/thesis_support/thesis_readiness.md")
    parser.add_argument("--json", default="reports/thesis_support/thesis_readiness.json")
    args = parser.parse_args()

    checks: list[dict[str, str]] = []

    # 1) 数据收集清洗与报告
    c1_paths = [
        "scripts/data/build_real_dataset.py",
        "scripts/data/run_data_governance_pipeline.py",
        "reports/real_dataset_report.md",
        "reports/data_cleaning_report.md",
    ]
    c1_ok = all(exists(x) for x in c1_paths)
    checks.append(
        {
            "id": "R1",
            "requirement": "数据收集、清洗与防泄露系统代码及数据统计报告",
            "status": "PASS" if c1_ok else "FAIL",
            "note": " | ".join(c1_paths),
        }
    )

    # 2) 可复现微调系统与最佳 checkpoint
    c2_status, c2_note = status_for_training_bundle(
        "reports/training/resource_skip_report.md",
        "reports/training/checkpoint_evidence.json",
    )
    checks.append(
        {
            "id": "R2",
            "requirement": "真实可复现微调系统（LoRA/QLoRA）及最优 checkpoint",
            "status": c2_status,
            "note": c2_note,
        }
    )

    # 3) API 自动评测多维度指标对比
    c3_paths = [
        "eval/llm_judge.py",
        "reports/eval_default.md",
        "reports/sota_compare.md",
        "reports/thesis_assets/tables/sota_compare_metrics.csv",
    ]
    c3_ok = all(exists(x) for x in c3_paths)
    checks.append(
        {
            "id": "R3",
            "requirement": "包含 API 自动评测的多维度指标对比表格",
            "status": "PASS" if c3_ok else "FAIL",
            "note": " | ".join(c3_paths),
        }
    )

    # 4) 真实训练 loss 曲线
    sft_metrics = load_json("reports/training/layer_b_qwen25_7b_sft_metrics.json")
    sft_mode = _training_mode(sft_metrics)
    curve_exists = has_real_sft_loss_curve()
    if sft_mode == "real" and curve_exists:
        c4_status = "PASS"
        c4_note = "已存在真实 SFT loss 曲线图"
    elif sft_mode in {"skipped", "simulation", "missing"} and exists("reports/training/resource_skip_report.md"):
        c4_status = "DEFERRED"
        c4_note = "真实 SFT 训练受限，当前仅具备跳过证据"
    else:
        c4_status = "FAIL"
        c4_note = f"缺失真实 SFT loss 曲线（sft_mode={sft_mode}）"
    checks.append(
        {
            "id": "R4",
            "requirement": "真实训练 Loss 下降曲线图（png/pdf）",
            "status": c4_status,
            "note": c4_note,
        }
    )

    # 5) 系统说明文档
    c5_paths = ["README.md", "docs/ARCH.md", "docs/DEPLOY.md", "docs/RESOURCE_AWARE_EXECUTION.md"]
    c5_ok = all(exists(x) for x in c5_paths)
    checks.append(
        {
            "id": "R5",
            "requirement": "系统说明文档（Readme、架构图、环境配置）",
            "status": "PASS" if c5_ok else "FAIL",
            "note": " | ".join(c5_paths),
        }
    )

    # 6) 论文初稿支撑材料
    c6_paths = [
        "reports/thesis_support/thesis_draft_material.md",
        "reports/thesis_support/experiment_record.json",
        "reports/error_analysis.md",
    ]
    c6_ok = all(exists(x) for x in c6_paths)
    checks.append(
        {
            "id": "R6",
            "requirement": "论文初稿支撑材料（实验记录、结论说明、创新点论述）",
            "status": "PASS" if c6_ok else "FAIL",
            "note": " | ".join(c6_paths),
        }
    )

    # 7) 评测偏差审计
    artifact_path = "reports/thesis_support/benchmark_artifact_report.json"
    artifact_v2_path = "reports/thesis_support/benchmark_artifact_report_v2_balanced.json"
    artifact = load_json(artifact_path)
    artifact_v2 = load_json(artifact_v2_path)
    if artifact_v2:
        leakage_v2 = str(artifact_v2.get("artifact_leakage_risk", "N/A")).upper()
        gap_v2 = artifact_v2.get("option_letter_gap_low_high", "N/A")
        if leakage_v2 == "LOW":
            c7_status = "PASS"
            c7_note = f"v2 偏差风险可接受（gap={gap_v2}），原始基准偏差已被隔离"
        elif leakage_v2 == "MEDIUM":
            c7_status = "DEFERRED"
            c7_note = f"v2 仍有中风险偏差（gap={gap_v2}），建议继续增强鲁棒消融"
        else:
            c7_status = "DEFERRED"
            c7_note = f"v2 偏差仍偏高（gap={gap_v2}），需进一步清洗构造规则"
    elif not artifact:
        c7_status = "FAIL"
        c7_note = f"缺失审计文件：{artifact_path}"
    else:
        leakage = str(artifact.get("artifact_leakage_risk", "N/A")).upper()
        gap = artifact.get("option_letter_gap_low_high", "N/A")
        if leakage == "HIGH":
            c7_status = "DEFERRED"
            c7_note = f"检测到高风险构造偏差（gap={gap}），需补 benchmark v2"
        elif leakage == "MEDIUM":
            c7_status = "DEFERRED"
            c7_note = f"检测到中风险构造偏差（gap={gap}），建议补充鲁棒消融"
        else:
            c7_status = "PASS"
            c7_note = f"构造偏差风险可接受（gap={gap}）"

    checks.append(
        {
            "id": "R7",
            "requirement": "评测偏差审计（避免格式泄露导致指标虚高）",
            "status": c7_status,
            "note": c7_note,
        }
    )

    counts = {"PASS": 0, "DEFERRED": 0, "FAIL": 0}
    for c in checks:
        counts[c["status"]] += 1

    report_lines = [
        "# Thesis Readiness Check",
        "",
        f"- PASS: {counts['PASS']}",
        f"- DEFERRED: {counts['DEFERRED']}",
        f"- FAIL: {counts['FAIL']}",
        f"- Ready (strict, no deferred): {counts['FAIL'] == 0 and counts['DEFERRED'] == 0}",
        f"- Ready (allow deferred): {counts['FAIL'] == 0}",
        "",
        "| ID | Requirement | Status | Note |",
        "|---|---|---|---|",
    ]
    for c in checks:
        report_lines.append(f"| {c['id']} | {c['requirement']} | {c['status']} | {c['note']} |")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    out_json = {
        "summary": counts,
        "ready_for_writing": counts["FAIL"] == 0 and counts["DEFERRED"] == 0,
        "ready_with_deferred": counts["FAIL"] == 0,
        "checks": checks,
    }
    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(out_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(out_json["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
