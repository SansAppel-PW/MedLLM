#!/usr/bin/env python3
"""Audit whether repository is ready for GPU migration mainline execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PASS = "PASS"
PARTIAL = "PARTIAL"
FAIL = "FAIL"


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check GPU migration readiness")
    parser.add_argument("--root", default=".")
    parser.add_argument("--opening-audit", default="reports/opening_alignment_audit.json")
    parser.add_argument("--out-md", default="reports/gpu_migration_readiness.md")
    parser.add_argument("--out-json", default="reports/gpu_migration_readiness.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    opening = load_json(root / args.opening_audit)
    checks = opening.get("checks", []) if isinstance(opening, dict) else []

    partial_ids = [str(x.get("id")) for x in checks if x.get("status") == PARTIAL]
    fail_ids = [str(x.get("id")) for x in checks if x.get("status") == FAIL]

    required_paths = [
        "scripts/train/run_gpu_thesis_mainline.sh",
        "scripts/train/run_layer_b_qwen_autofallback.sh",
        "scripts/train/run_real_alignment_pipeline.sh",
        "scripts/eval/run_thesis_pipeline.sh",
        "scripts/audit/verify_gpu_experiment_closure.py",
        "scripts/audit/check_opening_alignment.py",
        "scripts/audit/build_thesis_ready_package.py",
    ]
    missing_paths = [x for x in required_paths if not (root / x).exists()]

    dpo = load_json(root / "reports/training/dpo_real_metrics.json") or {}
    simpo = load_json(root / "reports/training/simpo_metrics.json") or {}
    kto = load_json(root / "reports/training/kto_metrics.json") or {}
    alignment_real_ready = all(
        [
            dpo.get("simulation") is False,
            simpo.get("simulation") is False,
            kto.get("simulation") is False,
        ]
    )

    blocker_detail = ""
    for row in checks:
        if row.get("id") == "A10":
            blocker_detail = str(row.get("detail", ""))
            break

    ready_for_gpu_run = len(fail_ids) == 0 and set(partial_ids).issubset({"A10"}) and not missing_paths
    status = "READY_FOR_GPU_MAINLINE" if ready_for_gpu_run else "NOT_READY"

    payload = {
        "status": status,
        "ready_for_gpu_run": ready_for_gpu_run,
        "opening_audit_partial_ids": partial_ids,
        "opening_audit_fail_ids": fail_ids,
        "remaining_primary_gap": "A10" if "A10" in partial_ids else None,
        "remaining_primary_gap_detail": blocker_detail,
        "alignment_real_ready": alignment_real_ready,
        "missing_required_paths": missing_paths,
        "gpu_execution_commands": [
            "python -m pip install -r requirements.txt",
            "bash scripts/train/run_gpu_thesis_mainline.sh",
            "python scripts/audit/verify_gpu_experiment_closure.py --strict",
            "python scripts/audit/check_opening_alignment.py",
        ],
    }

    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# GPU Migration Readiness",
        "",
        f"- Status: {payload['status']}",
        f"- Ready for GPU mainline run: {payload['ready_for_gpu_run']}",
        f"- Opening audit partial IDs: {', '.join(partial_ids) if partial_ids else 'None'}",
        f"- Opening audit fail IDs: {', '.join(fail_ids) if fail_ids else 'None'}",
        f"- Alignment real-ready (DPO/SimPO/KTO): {alignment_real_ready}",
        f"- Missing required paths: {', '.join(missing_paths) if missing_paths else 'None'}",
        "",
        "## Remaining Primary Gap",
        f"- {payload['remaining_primary_gap'] or 'None'}: {payload['remaining_primary_gap_detail'] or 'N/A'}",
        "",
        "## GPU Execution Commands",
    ]
    for cmd in payload["gpu_execution_commands"]:
        lines.append(f"- `{cmd}`")

    out_md = root / args.out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": status, "ready_for_gpu_run": ready_for_gpu_run}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

