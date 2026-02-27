#!/usr/bin/env python3
"""Verify whether GPU mainline experiment closure artifacts are complete."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PASS = "PASS"
FAIL = "FAIL"


@dataclass
class CheckResult:
    id: str
    requirement: str
    status: str
    detail: str
    evidence: list[str]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify GPU experiment closure artifacts")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-md", default="reports/gpu_experiment_closure.md")
    parser.add_argument("--out-json", default="reports/gpu_experiment_closure.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results: list[CheckResult] = []

    layer_b = load_json(root / "reports/training/layer_b_qwen25_7b_sft_metrics.json")
    layer_b_ok = bool(layer_b and is_number(layer_b.get("train_loss")))
    results.append(
        CheckResult(
            id="G01",
            requirement="Layer-B Qwen2.5-7B real SFT metrics",
            status=PASS if layer_b_ok else FAIL,
            detail="Layer-B metrics present with numeric train_loss." if layer_b_ok else "Missing Layer-B metrics or invalid train_loss.",
            evidence=["reports/training/layer_b_qwen25_7b_sft_metrics.json"],
        )
    )

    dpo = load_json(root / "reports/training/dpo_real_metrics.json")
    dpo_ok = bool(dpo and dpo.get("simulation") is False and int(dpo.get("pair_count", 0)) > 0)
    results.append(
        CheckResult(
            id="G02",
            requirement="Real DPO alignment evidence",
            status=PASS if dpo_ok else FAIL,
            detail="DPO metrics are real and pair_count>0." if dpo_ok else "DPO metrics missing or still simulated.",
            evidence=["reports/training/dpo_real_metrics.json"],
        )
    )

    simpo = load_json(root / "reports/training/simpo_metrics.json")
    simpo_ok = bool(simpo and simpo.get("simulation") is False and int(simpo.get("pair_count", simpo.get("samples", 0))) > 0)
    results.append(
        CheckResult(
            id="G03",
            requirement="Real SimPO alignment evidence",
            status=PASS if simpo_ok else FAIL,
            detail="SimPO metrics are real and sample_count>0." if simpo_ok else "SimPO metrics missing or still simulated.",
            evidence=["reports/training/simpo_metrics.json"],
        )
    )

    kto = load_json(root / "reports/training/kto_metrics.json")
    kto_ok = bool(kto and kto.get("simulation") is False and int(kto.get("pair_count", kto.get("samples", 0))) > 0)
    results.append(
        CheckResult(
            id="G04",
            requirement="Real KTO alignment evidence",
            status=PASS if kto_ok else FAIL,
            detail="KTO metrics are real and sample_count>0." if kto_ok else "KTO metrics missing or still simulated.",
            evidence=["reports/training/kto_metrics.json"],
        )
    )

    opening = load_json(root / "reports/opening_alignment_audit.json")
    a10_status = None
    if opening:
        for row in opening.get("checks", []):
            if row.get("id") == "A10":
                a10_status = row.get("status")
                break
    a10_ok = a10_status == PASS
    results.append(
        CheckResult(
            id="G05",
            requirement="Opening alignment A10 should be PASS",
            status=PASS if a10_ok else FAIL,
            detail=f"A10 status={a10_status}." if a10_status else "A10 not found in opening alignment audit.",
            evidence=["reports/opening_alignment_audit.json"],
        )
    )

    main_real_csv = root / "reports/thesis_assets/tables/main_results_real.csv"
    real_csv_text = main_real_csv.read_text(encoding="utf-8") if main_real_csv.exists() else ""
    layer_b_row_ok = "Qwen2.5-7B Layer-B" in real_csv_text
    results.append(
        CheckResult(
            id="G06",
            requirement="Main real result table should include Layer-B row",
            status=PASS if layer_b_row_ok else FAIL,
            detail="Layer-B row is present in main_results_real.csv." if layer_b_row_ok else "Layer-B row not found in main_results_real.csv.",
            evidence=["reports/thesis_assets/tables/main_results_real.csv"],
        )
    )

    summary = {
        "total": len(results),
        "pass": sum(1 for x in results if x.status == PASS),
        "fail": sum(1 for x in results if x.status == FAIL),
    }

    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps({"summary": summary, "checks": [x.__dict__ for x in results]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# GPU Experiment Closure Verification",
        "",
        f"- PASS: {summary['pass']}",
        f"- FAIL: {summary['fail']}",
        "",
        "| ID | Requirement | Status | Detail | Evidence |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row.id} | {row.requirement} | {row.status} | {row.detail} | {'<br>'.join(row.evidence)} |"
        )

    out_md = root / args.out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    if args.strict and summary["fail"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

