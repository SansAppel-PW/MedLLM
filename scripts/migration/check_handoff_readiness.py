#!/usr/bin/env python3
"""Audit whether repository is ready for GPU handoff execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_PATHS = [
    "scripts/migration/bootstrap_gpu_env.sh",
    "scripts/migration/run_gpu_thesis_experiment.sh",
    "scripts/migration/build_gpu_handoff_manifest.py",
    "docs/GPU_MIGRATION_RUNBOOK.md",
    "scripts/train/run_real_alignment_pipeline.sh",
    "scripts/eval/run_thesis_pipeline.sh",
    "scripts/pipeline/run_paper_ready.sh",
    "reports/pipeline/paper_ready_status.md",
    "reports/thesis_support/thesis_readiness.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check GPU handoff readiness")
    parser.add_argument("--report", default="reports/migration/handoff_readiness.md")
    parser.add_argument("--json", default="reports/migration/handoff_readiness.json")
    args = parser.parse_args()

    checks = []
    for rel in REQUIRED_PATHS:
        ok = Path(rel).exists()
        checks.append({"path": rel, "exists": ok})

    missing = [x["path"] for x in checks if not x["exists"]]
    payload = {
        "ready": len(missing) == 0,
        "missing_count": len(missing),
        "missing": missing,
        "checks": checks,
    }

    report_lines = [
        "# GPU Handoff Readiness",
        "",
        f"- Ready: {payload['ready']}",
        f"- Missing count: {payload['missing_count']}",
        "",
        "| path | exists |",
        "|---|---|",
    ]
    for item in checks:
        report_lines.append(f"| {item['path']} | {item['exists']} |")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ready": payload["ready"], "missing_count": payload["missing_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
