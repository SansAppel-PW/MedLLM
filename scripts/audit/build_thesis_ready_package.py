#!/usr/bin/env python3
"""Build thesis-ready summary artifacts from current experiment outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_json(path: Path) -> dict[str, Any] | None:
    if path.exists():
        return load_json(path)
    return None


def run_order(tag: str) -> tuple[int, str]:
    m = re.search(r"small_real_lora_v(\d+)$", tag)
    if m:
        return (int(m.group(1)), tag)
    return (-1, tag)


def collect_small_real_runs(root: Path) -> list[dict[str, Any]]:
    train_dir = root / "reports/training"
    rows: list[dict[str, Any]] = []
    for train_path in train_dir.glob("small_real_lora_v*_metrics.json"):
        tag = train_path.stem.replace("_metrics", "")
        eval_path = root / f"reports/small_real/{tag}/eval_metrics.json"
        if not eval_path.exists():
            continue
        train_metrics = load_json(train_path)
        eval_metrics = load_json(eval_path)
        rows.append(
            {
                "run_tag": tag,
                "train_metrics_path": str(train_path.relative_to(root)),
                "eval_metrics_path": str(eval_path.relative_to(root)),
                "train_loss": train_metrics.get("train_loss"),
                "final_eval_loss": train_metrics.get("final_eval_loss"),
                "exact_match": eval_metrics.get("exact_match"),
                "rouge_l_f1": eval_metrics.get("rouge_l_f1"),
                "char_f1": eval_metrics.get("char_f1"),
            }
        )
    rows.sort(key=lambda x: run_order(str(x["run_tag"])))
    return rows


def collect_dpo_runs(root: Path) -> list[dict[str, Any]]:
    train_dir = root / "reports/training"
    rows: list[dict[str, Any]] = []
    dpo_files = list(train_dir.glob("small_real_dpo_v*_metrics.json"))
    mainline = train_dir / "dpo_real_metrics.json"
    if mainline.exists():
        dpo_files.append(mainline)

    for mpath in dpo_files:
        tag = mpath.stem.replace("_metrics", "")
        metrics = load_json(mpath)
        rows.append(
            {
                "run_tag": tag,
                "simulation": metrics.get("simulation"),
                "pair_count": metrics.get("pair_count"),
                "steps": metrics.get("steps"),
                "train_loss": metrics.get("train_loss"),
                "pref_accuracy_before": metrics.get("pref_accuracy_before"),
                "pref_accuracy_after": metrics.get("pref_accuracy_after"),
                "pref_accuracy_gain": metrics.get("pref_accuracy_gain"),
                "metrics_path": str(mpath.relative_to(root)),
            }
        )
    rows.sort(key=lambda x: run_order(str(x["run_tag"])))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build thesis-ready package artifacts")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--out-md", default="reports/thesis_assets/thesis_ready_summary.md")
    parser.add_argument("--out-json", default="reports/thesis_assets/thesis_ready_summary.json")
    parser.add_argument("--main-csv", default="reports/thesis_assets/tables/main_results_small_real.csv")
    parser.add_argument("--ablation-csv", default="reports/thesis_assets/tables/ablation_small_real_runs.csv")
    parser.add_argument("--dpo-csv", default="reports/thesis_assets/tables/alignment_real_dpo_runs.csv")
    parser.add_argument("--dpo-beta-csv", default="reports/thesis_assets/tables/dpo_beta_ablation.csv")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    dpo_beta_csv = root / args.dpo_beta_csv
    runs = collect_small_real_runs(root)
    latest = runs[-1] if runs else None
    dpo_runs = collect_dpo_runs(root)
    latest_dpo = dpo_runs[-1] if dpo_runs else None

    base_eval = maybe_json(root / "reports/small_real/base_model_eval_metrics.json")
    qwen_blocker = root / "reports/small_real/qwen_layer_b_blocker.md"
    baseline_table = root / "reports/thesis_assets/tables/baseline_audit_table.csv"
    error_cases = root / "reports/thesis_assets/cases/error_cases_top30.jsonl"

    main_rows: list[dict[str, Any]] = []
    if base_eval:
        main_rows.append(
            {
                "setting": "BaseModel (tiny-gpt2)",
                "run_tag": "base_model",
                "exact_match": base_eval.get("exact_match"),
                "rouge_l_f1": base_eval.get("rouge_l_f1"),
                "char_f1": base_eval.get("char_f1"),
                "train_loss": None,
                "final_eval_loss": None,
                "evidence": "reports/small_real/base_model_eval_metrics.json",
            }
        )
    if latest:
        main_rows.append(
            {
                "setting": "LoRA Small-Real",
                "run_tag": latest["run_tag"],
                "exact_match": latest.get("exact_match"),
                "rouge_l_f1": latest.get("rouge_l_f1"),
                "char_f1": latest.get("char_f1"),
                "train_loss": latest.get("train_loss"),
                "final_eval_loss": latest.get("final_eval_loss"),
                "evidence": latest.get("eval_metrics_path"),
            }
        )

    write_csv(
        root / args.main_csv,
        main_rows,
        [
            "setting",
            "run_tag",
            "exact_match",
            "rouge_l_f1",
            "char_f1",
            "train_loss",
            "final_eval_loss",
            "evidence",
        ],
    )
    write_csv(
        root / args.ablation_csv,
        runs,
        [
            "run_tag",
            "train_loss",
            "final_eval_loss",
            "exact_match",
            "rouge_l_f1",
            "char_f1",
            "train_metrics_path",
            "eval_metrics_path",
        ],
    )
    write_csv(
        root / args.dpo_csv,
        dpo_runs,
        [
            "run_tag",
            "simulation",
            "pair_count",
            "steps",
            "train_loss",
            "pref_accuracy_before",
            "pref_accuracy_after",
            "pref_accuracy_gain",
            "metrics_path",
        ],
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "latest_small_real_run": latest["run_tag"] if latest else None,
        "latest_small_real_dpo_run": latest_dpo["run_tag"] if latest_dpo else None,
        "artifacts": {
            "main_results_csv": args.main_csv,
            "ablation_csv": args.ablation_csv,
            "real_dpo_csv": args.dpo_csv,
            "dpo_beta_ablation_csv": args.dpo_beta_csv if dpo_beta_csv.exists() else None,
            "baseline_audit_table": str(baseline_table.relative_to(root)) if baseline_table.exists() else None,
            "qwen_blocker": str(qwen_blocker.relative_to(root)) if qwen_blocker.exists() else None,
            "error_cases": str(error_cases.relative_to(root)) if error_cases.exists() else None,
        },
        "paper_ready_notes": {
            "main_result_scope": "Small-Real LoRA fallback evidence (engineering closure), not final thesis mainline.",
            "ablation_scope": "Across small_real_lora_v* runs to verify reproducibility and run stability.",
            "alignment_scope": "Small-Real DPO real-training runs (if available) as alignment evidence.",
            "limitation": "Qwen2.5-7B Layer-B full experiment blocked by missing GPU/CUDA resources in current environment.",
            "next_action": "Run scripts/train/run_layer_b_qwen_autofallback.sh on >=24GB GPU and regenerate package.",
        },
    }

    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Thesis Ready Summary",
        "",
        f"- Generated(UTC): {payload['generated_at_utc']}",
        f"- Latest Small-Real Run: {payload['latest_small_real_run']}",
        "",
        "## Main Result Table",
        f"- CSV: `{args.main_csv}`",
        "",
        "## Ablation/Control Table",
        f"- CSV: `{args.ablation_csv}`",
        "",
        "## Alignment (Real DPO) Table",
        f"- CSV: `{args.dpo_csv}`",
        "",
        "## DPO Beta Ablation",
        f"- CSV: `{args.dpo_beta_csv}`",
        "",
        "## Supporting Evidence",
        f"- Baseline Audit: `{payload['artifacts']['baseline_audit_table']}`",
        f"- Qwen Layer-B Blocker: `{payload['artifacts']['qwen_blocker']}`",
        f"- Error Cases: `{payload['artifacts']['error_cases']}`",
        "",
        "## Thesis Writing Notes",
        f"- 主结果口径: {payload['paper_ready_notes']['main_result_scope']}",
        f"- 消融口径: {payload['paper_ready_notes']['ablation_scope']}",
        f"- 对齐口径: {payload['paper_ready_notes']['alignment_scope']}",
        f"- 局限性: {payload['paper_ready_notes']['limitation']}",
        f"- 下一步: {payload['paper_ready_notes']['next_action']}",
    ]
    out_md = root / args.out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[thesis-ready-package] md={args.out_md} json={args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
