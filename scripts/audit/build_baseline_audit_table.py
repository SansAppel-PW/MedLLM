#!/usr/bin/env python3
"""Build auditable baseline comparison table for thesis writing."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any


def path_exists(path: str) -> bool:
    return Path(path).exists()


def resolve_small_real_eval_path(run_tag: str | None) -> str:
    if run_tag:
        candidate = Path("reports/small_real") / run_tag / "eval_metrics.json"
        if candidate.exists():
            return str(candidate)
    base = Path("reports/small_real")
    candidates = [p / "eval_metrics.json" for p in base.glob("small_real_lora_v*/") if (p / "eval_metrics.json").exists()]
    if not candidates:
        return "reports/small_real/small_real_lora_v3/eval_metrics.json"
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return str(latest)


def build_rows(run_tag: str | None) -> list[dict[str, Any]]:
    sota_report = "reports/sota_compare.md"
    small_real_metrics = resolve_small_real_eval_path(run_tag)
    qwen_blocker = "reports/small_real/qwen_layer_b_blocker.md"

    rows = [
        {
            "model": "Med-PaLM 2",
            "method": "Closed-source medical instruction tuning + ensemble refinement",
            "data_setup": "Internal large-scale medical corpora (not fully open)",
            "key_metrics_scope": "USMLE / expert-level QA (paper-reported)",
            "cost_level": "Very High",
            "reproducibility": "Low (closed weights/training data)",
            "local_run_status": "Not runnable locally",
            "audit_evidence": "docs/OPENING_PROPOSAL_EVIDENCE.md",
            "limitations": "Cannot perform fair local retraining/ablation",
            "evidence_layer": "proxy-background",
            "comparability": "background-only",
        },
        {
            "model": "ChatDoctor",
            "method": "LLaMA-family supervised fine-tuning on medical dialogues",
            "data_setup": "Open dialogue corpora + external medical KB",
            "key_metrics_scope": "Dialogue quality / medical QA correctness",
            "cost_level": "Medium",
            "reproducibility": "Medium (open recipe, environment-sensitive)",
            "local_run_status": "Background baseline (not fully rerun in this repo)",
            "audit_evidence": "docs/OPENING_PROPOSAL_EVIDENCE.md",
            "limitations": "Original training stack/version drift risk",
            "evidence_layer": "proxy-background",
            "comparability": "background-only",
        },
        {
            "model": "HuatuoGPT / HuatuoGPT-II",
            "method": "Chinese medical adaptation + SFT/alignment",
            "data_setup": "Chinese medical corpora and QA datasets",
            "key_metrics_scope": "Chinese medical QA benchmarks",
            "cost_level": "High",
            "reproducibility": "Medium",
            "local_run_status": "Proxy compared" if path_exists(sota_report) else "Planned",
            "audit_evidence": sota_report if path_exists(sota_report) else "docs/EXPERIMENT_MASTER_PLAN.md",
            "limitations": "Current repo comparison is proxy-level, not full official reproduction",
            "evidence_layer": "proxy-background",
            "comparability": "background-only",
        },
        {
            "model": "DISC-MedLLM",
            "method": "Instruction-tuned Chinese medical LLM baseline",
            "data_setup": "Chinese instruction and medical QA style corpora",
            "key_metrics_scope": "Medical QA / instruction-following",
            "cost_level": "High",
            "reproducibility": "Medium",
            "local_run_status": "Planned (table-level baseline)",
            "audit_evidence": "docs/EXPERIMENT_MASTER_PLAN.md",
            "limitations": "No local full retraining execution yet",
            "evidence_layer": "proxy-background",
            "comparability": "background-only",
        },
        {
            "model": "Qwen2.5-7B-Instruct (target mainline)",
            "method": "QLoRA/LoRA SFT + alignment (DPO/SimPO planned)",
            "data_setup": "Repo real_* datasets + KG-governed pipeline",
            "key_metrics_scope": "FactScore / safety / utility / ablation",
            "cost_level": "Medium-High",
            "reproducibility": "High (scripts + manifests + guard)",
            "local_run_status": "Blocked by GPU" if path_exists(qwen_blocker) else "Running/Ready",
            "audit_evidence": qwen_blocker if path_exists(qwen_blocker) else small_real_metrics,
            "limitations": "Needs CUDA memory to execute Layer-B full run",
            "evidence_layer": "real-mainline",
            "comparability": "thesis-mainline",
        },
        {
            "model": "TinyGPT2-LoRA (small-real fallback)",
            "method": "Offline LoRA real training fallback path",
            "data_setup": "Current minimal clean split (engineering validation)",
            "key_metrics_scope": "EM / Rouge-L / Char-F1 (small-real sanity metrics)",
            "cost_level": "Low",
            "reproducibility": "High",
            "local_run_status": "Completed" if path_exists(small_real_metrics) else "Planned",
            "audit_evidence": small_real_metrics if path_exists(small_real_metrics) else "reports/small_real/",
            "limitations": "Not thesis main model; only pipeline closure evidence",
            "evidence_layer": "real-mainline",
            "comparability": "fallback-evidence",
        },
    ]
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build baseline audit table")
    parser.add_argument(
        "--small-real-run-tag",
        default=os.getenv("RUN_TAG"),
        help="Optional small-real run tag; if omitted, resolve latest available run",
    )
    parser.add_argument("--out-csv", default="reports/thesis_assets/tables/baseline_audit_table.csv")
    parser.add_argument("--out-md", default="reports/baseline_audit_table.md")
    parser.add_argument("--out-json", default="reports/thesis_assets/tables/baseline_audit_table.json")
    parser.add_argument(
        "--out-real-csv",
        default="reports/thesis_assets/tables/baseline_real_mainline.csv",
    )
    parser.add_argument(
        "--out-proxy-csv",
        default="reports/thesis_assets/tables/baseline_proxy_background.csv",
    )
    parser.add_argument(
        "--out-dual-md",
        default="reports/thesis_assets/tables/baseline_audit_dual_view.md",
    )
    args = parser.parse_args()

    rows = build_rows(args.small_real_run_tag)
    real_rows = [x for x in rows if x.get("evidence_layer") == "real-mainline"]
    proxy_rows = [x for x in rows if x.get("evidence_layer") == "proxy-background"]

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "method",
        "data_setup",
        "key_metrics_scope",
        "cost_level",
        "reproducibility",
        "local_run_status",
        "audit_evidence",
        "limitations",
        "evidence_layer",
        "comparability",
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    for out_path, subset in ((Path(args.out_real_csv), real_rows), (Path(args.out_proxy_csv), proxy_rows)):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in subset:
                writer.writerow(row)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "all": rows,
                "real_mainline": real_rows,
                "proxy_background": proxy_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        "# 医学LLM Baseline 可审计对比表",
        "",
        "| 模型 | 方法 | 数据 | 指标范围 | 成本 | 可复现性 | 本仓库状态 | 审计证据 | 局限 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['model']} | {row['method']} | {row['data_setup']} | "
            f"{row['key_metrics_scope']} | {row['cost_level']} | {row['reproducibility']} | "
            f"{row['local_run_status']} | `{row['audit_evidence']}` | {row['limitations']} |"
        )
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    dual_lines = [
        "# Baseline Audit Dual View",
        "",
        "> 口径说明：`real-mainline` 用于论文主结果路径；`proxy-background` 仅用于背景/相关工作，不与 real 指标直接数值比较。",
        "",
        "## Real Mainline",
        "| 模型 | 方法 | 数据 | 指标范围 | 成本 | 可复现性 | 本仓库状态 | 审计证据 | 局限 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in real_rows:
        dual_lines.append(
            f"| {row['model']} | {row['method']} | {row['data_setup']} | "
            f"{row['key_metrics_scope']} | {row['cost_level']} | {row['reproducibility']} | "
            f"{row['local_run_status']} | `{row['audit_evidence']}` | {row['limitations']} |"
        )
    dual_lines.extend(
        [
            "",
            "## Proxy Background",
            "| 模型 | 方法 | 数据 | 指标范围 | 成本 | 可复现性 | 本仓库状态 | 审计证据 | 局限 |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in proxy_rows:
        dual_lines.append(
            f"| {row['model']} | {row['method']} | {row['data_setup']} | "
            f"{row['key_metrics_scope']} | {row['cost_level']} | {row['reproducibility']} | "
            f"{row['local_run_status']} | `{row['audit_evidence']}` | {row['limitations']} |"
        )
    out_dual_md = Path(args.out_dual_md)
    out_dual_md.parent.mkdir(parents=True, exist_ok=True)
    out_dual_md.write_text("\n".join(dual_lines) + "\n", encoding="utf-8")

    print(
        "[baseline-audit] "
        f"rows={len(rows)} real={len(real_rows)} proxy={len(proxy_rows)} "
        f"csv={out_csv} md={out_md} dual_md={out_dual_md} json={out_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
