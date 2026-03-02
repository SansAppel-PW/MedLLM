#!/usr/bin/env python3
"""Check readiness for one-shot GPU harvest execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PASS = "PASS"
FAIL = "FAIL"


def check_exists(root: Path, rels: list[str]) -> tuple[bool, list[str]]:
    missing = [r for r in rels if not (root / r).exists()]
    return len(missing) == 0, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Check one-shot GPU harvest readiness")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-json", default="reports/gpu_once_readiness.json")
    parser.add_argument("--out-md", default="reports/gpu_once_readiness.md")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    checks: list[dict[str, Any]] = []

    entry_scripts = [
        "day1_run.sh",
        "scripts/train/run_gpu_thesis_mainline.sh",
        "scripts/deploy/run_gpu_once_harvest.sh",
        "scripts/deploy/package_thesis_bundle.py",
        "scripts/eval/build_thesis_figures.py",
    ]
    ok, missing = check_exists(root, entry_scripts)
    checks.append(
        {
            "id": "R01",
            "item": "主执行入口脚本齐全",
            "status": PASS if ok else FAIL,
            "detail": "all present" if ok else f"missing: {', '.join(missing)}",
            "evidence": entry_scripts,
        }
    )

    makefile = (root / "Makefile").read_text(encoding="utf-8") if (root / "Makefile").exists() else ""
    targets = ["gpu-mainline:", "thesis-ready:", "gpu-once-harvest:", "thesis-bundle:", "next-stage:"]
    target_missing = [t for t in targets if t not in makefile]
    checks.append(
        {
            "id": "R02",
            "item": "Makefile 目标齐全",
            "status": PASS if not target_missing else FAIL,
            "detail": "all present" if not target_missing else f"missing: {', '.join(target_missing)}",
            "evidence": ["Makefile"],
        }
    )

    data_scripts = [
        "scripts/data/ensure_real_dataset.sh",
        "scripts/data/build_cm3kg_real_assets.py",
        "scripts/data/build_unified_real_assets.py",
        "scripts/eval/run_thesis_pipeline.sh",
    ]
    ok_data, missing_data = check_exists(root, data_scripts)
    checks.append(
        {
            "id": "R03",
            "item": "数据/KG/评测链路脚本齐全",
            "status": PASS if ok_data else FAIL,
            "detail": "all present" if ok_data else f"missing: {', '.join(missing_data)}",
            "evidence": data_scripts,
        }
    )

    expected_tables = [
        "reports/thesis_assets/tables/main_results_real.csv",
        "reports/thesis_assets/tables/baseline_audit_table.csv",
        "reports/thesis_assets/tables/conclusion_status_dashboard.csv",
    ]
    ok_tables, missing_tables = check_exists(root, expected_tables)
    checks.append(
        {
            "id": "R04",
            "item": "关键表格模板/历史产物存在",
            "status": PASS if ok_tables else FAIL,
            "detail": "all present" if ok_tables else f"missing: {', '.join(missing_tables)}",
            "evidence": expected_tables,
        }
    )

    expected_fig_entries = [
        "reports/thesis_assets/figures/figure_manifest.json",
        "reports/thesis_assets/figures/conclusion_dashboard_mermaid.md",
    ]
    ok_fig, missing_fig = check_exists(root, expected_fig_entries)
    checks.append(
        {
            "id": "R05",
            "item": "图表产线入口存在",
            "status": PASS if ok_fig else FAIL,
            "detail": "all present" if ok_fig else f"missing: {', '.join(missing_fig)}",
            "evidence": expected_fig_entries,
        }
    )

    summary = {
        "total": len(checks),
        "pass": sum(1 for c in checks if c["status"] == PASS),
        "fail": sum(1 for c in checks if c["status"] == FAIL),
    }
    payload = {"summary": summary, "checks": checks}

    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# GPU Once Readiness",
        "",
        f"- total: {summary['total']}",
        f"- pass: {summary['pass']}",
        f"- fail: {summary['fail']}",
        "",
        "| ID | 项目 | 状态 | 细节 |",
        "|---|---|---|---|",
    ]
    for c in checks:
        lines.append(f"| {c['id']} | {c['item']} | {c['status']} | {c['detail']} |")
    (root / args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
