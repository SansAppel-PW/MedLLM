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
    args = parser.parse_args()

    rows = build_rows(args.small_real_run_tag)

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
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

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

    print(f"[baseline-audit] rows={len(rows)} csv={out_csv} md={out_md} json={out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
