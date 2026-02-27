#!/usr/bin/env python3
"""Strict completion gate for post-GPU thesis experiments."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_real_metric(payload: dict[str, Any]) -> bool:
    if not payload:
        return False
    if bool(payload.get("skipped", False)):
        return False
    if bool(payload.get("simulation", False)):
        return False
    return True


def load_checkpoint_evidence(path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(path)
    comps = payload.get("components", {}) if isinstance(payload, dict) else {}
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(comps, dict):
        return out
    for name, item in comps.items():
        if isinstance(item, dict):
            out[str(name)] = item
    return out


def has_real_sft_curve() -> bool:
    direct = [
        Path("reports/thesis_assets/figures/training_loss_qwen25_7b_sft.png"),
        Path("reports/thesis_assets/figures/training_loss_layer_b_qwen25_7b_sft.png"),
    ]
    if any(p.exists() for p in direct):
        return True

    rows = load_csv_rows(Path("reports/thesis_assets/tables/training_loss_summary.csv"))
    for row in rows:
        if str(row.get("source_log", "")) != "logs/layer_b/qwen25_7b_sft/train_log.jsonl":
            continue
        try:
            points = int(float(str(row.get("points", "0"))))
        except ValueError:
            points = 0
        fig = Path(str(row.get("figure", "")))
        if points > 0 and fig.exists():
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict post-GPU completion check")
    parser.add_argument("--thesis-readiness-json", default="reports/thesis_support/thesis_readiness.json")
    parser.add_argument("--report", default="reports/migration/gpu_completion_check.md")
    parser.add_argument("--json", default="reports/migration/gpu_completion_check.json")
    parser.add_argument("--allow-deferred", action="store_true", help="Allow thesis readiness DEFERRED > 0")
    args = parser.parse_args()
    checkpoint_evidence = load_checkpoint_evidence(Path("reports/training/checkpoint_evidence.json"))

    specs = [
        ("SFT", Path("reports/training/layer_b_qwen25_7b_sft_metrics.json"), Path("checkpoints/layer_b/qwen25_7b_sft/final")),
        ("DPO", Path("reports/training/dpo_metrics.json"), Path("checkpoints/dpo-real-baseline/final")),
        ("SimPO", Path("reports/training/simpo_metrics.json"), Path("checkpoints/simpo-real-baseline/final")),
        ("KTO", Path("reports/training/kto_metrics.json"), Path("checkpoints/kto-real-baseline/final")),
    ]

    rows: list[dict[str, Any]] = []
    hard_fail = False

    for name, metrics_path, ckpt_path in specs:
        metrics = load_json(metrics_path)
        metric_exists = bool(metrics)
        metric_real = is_real_metric(metrics)
        ckpt_exists = ckpt_path.exists()
        evidence = checkpoint_evidence.get(name, {})
        ckpt_evidence_exists = bool(evidence.get("verified", False))
        ckpt_effective_exists = ckpt_exists or ckpt_evidence_exists

        note = ""
        if not metric_exists:
            note = "metrics missing"
            hard_fail = True
        elif not metric_real:
            note = "metrics marked skipped/simulation"
            hard_fail = True
        elif not ckpt_effective_exists:
            note = "checkpoint final directory missing"
            hard_fail = True
        else:
            if name == "SFT":
                if metrics.get("train_loss") is None:
                    note = "train_loss missing"
                    hard_fail = True
                else:
                    if ckpt_exists:
                        note = "real metrics + checkpoint present"
                    else:
                        note = "real metrics + checkpoint evidence present"
            else:
                try:
                    steps = int(metrics.get("global_steps", 0))
                except (TypeError, ValueError):
                    steps = 0
                if steps <= 0:
                    note = "global_steps <= 0"
                    hard_fail = True
                else:
                    if ckpt_exists:
                        note = "real metrics + checkpoint present"
                    else:
                        note = "real metrics + checkpoint evidence present"

        rows.append(
            {
                "component": name,
                "metrics_path": str(metrics_path),
                "metrics_exists": metric_exists,
                "metrics_real": metric_real,
                "checkpoint_path": str(ckpt_path),
                "checkpoint_exists": ckpt_exists,
                "checkpoint_evidence_exists": ckpt_evidence_exists,
                "checkpoint_effective_exists": ckpt_effective_exists,
                "note": note,
            }
        )

    sft_curve_ok = has_real_sft_curve()
    if not sft_curve_ok:
        hard_fail = True

    thesis_payload = load_json(Path(args.thesis_readiness_json))
    summary = thesis_payload.get("summary", {}) if thesis_payload else {}
    fail_raw = summary.get("FAIL", 0)
    deferred_raw = summary.get("DEFERRED", 0)
    fail_count = int(fail_raw) if isinstance(fail_raw, (int, float)) else 0
    deferred_count = int(deferred_raw) if isinstance(deferred_raw, (int, float)) else 0

    if fail_count > 0:
        hard_fail = True
    if (not args.allow_deferred) and deferred_count > 0:
        hard_fail = True

    payload = {
        "strict_pass": not hard_fail,
        "allow_deferred": bool(args.allow_deferred),
        "thesis_readiness": {
            "fail": fail_count,
            "deferred": deferred_count,
            "path": args.thesis_readiness_json,
        },
        "real_sft_curve_present": sft_curve_ok,
        "components": rows,
    }

    report_lines = [
        "# GPU Completion Check",
        "",
        f"- strict_pass: {payload['strict_pass']}",
        f"- allow_deferred: {payload['allow_deferred']}",
        f"- thesis_readiness_fail: {fail_count}",
        f"- thesis_readiness_deferred: {deferred_count}",
        f"- real_sft_curve_present: {sft_curve_ok}",
        "",
        "| component | metrics_exists | metrics_real | checkpoint_exists | note |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['component']} | {row['metrics_exists']} | {row['metrics_real']} | {row['checkpoint_effective_exists']} | {row['note']} |"
        )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"strict_pass": payload["strict_pass"]}, ensure_ascii=False))
    return 0 if payload["strict_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
