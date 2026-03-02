#!/usr/bin/env python3
"""Package thesis-ready artifacts into a portable bundle with checksums."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: str) -> tuple[int, str]:
    import subprocess

    proc = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        if err:
            out = f"{out}\n{err}".strip()
    return proc.returncode, out


def copy_path(src_root: Path, dst_root: Path, rel: str) -> dict[str, Any] | None:
    src = src_root / rel
    if not src.exists():
        return None
    dst = dst_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return {"path": rel, "type": "dir"}
    shutil.copy2(src, dst)
    return {"path": rel, "type": "file", "bytes": src.stat().st_size, "sha256": sha256(src)}


def iter_files(root: Path) -> list[Path]:
    rows: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            rows.append(p)
    rows.sort()
    return rows


def line_count_jsonl(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    if path.suffix != ".jsonl":
        return None
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build portable thesis artifact bundle")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-dir", default="exports")
    parser.add_argument("--tag", default=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--include-logs", action="store_true", default=False)
    parser.add_argument("--include-clean-data", action="store_true", default=False)
    parser.add_argument("--archive", action="store_true", default=True)
    args = parser.parse_args()

    src_root = Path(args.root).resolve()
    out_base = (src_root / args.out_dir).resolve()
    bundle_name = f"thesis_bundle_{args.tag}"
    bundle_root = out_base / bundle_name
    bundle_root.mkdir(parents=True, exist_ok=True)

    include_paths = [
        "reports",
        "docs/EXECUTION_TASKS.md",
        "docs/OPENING_PROPOSAL_EVIDENCE.md",
        "docs/EXPERIMENT_MASTER_PLAN.md",
        "docs/THESIS_WRITING_MATERIALS.md",
        "docs/PROJECT_STATUS_AUDIT.md",
        "docs/DECISION_LOG.md",
        "README.md",
        "Makefile",
        "requirements.txt",
        "configs",
    ]
    if args.include_logs:
        include_paths.extend(
            [
                "logs/session",
                "logs/layer_b",
                "logs/dpo-real-baseline",
                "logs/simpo-real-baseline",
                "logs/kto-real-baseline",
                "logs/small_real",
                "logs/alignment",
            ]
        )
    if args.include_clean_data:
        include_paths.extend(
            [
                "data/clean/real_sft_train.jsonl",
                "data/clean/real_sft_dev.jsonl",
                "data/clean/real_sft_test.jsonl",
                "data/clean/real_pref_seed_pairs.jsonl",
                "data/benchmark/real_medqa_benchmark.jsonl",
                "data/benchmark/real_medqa_benchmark_balanced.jsonl",
                "data/kg/cm3kg_merged_triples.jsonl",
                "data/kg/cm3kg_merged_kb.jsonl",
                "reports/real_dataset_summary.json",
                "reports/real_dataset_report.md",
                "reports/cm3kg_dataset_summary.json",
                "reports/cm3kg_dataset_report.md",
            ]
        )

    copied: list[dict[str, Any]] = []
    for rel in include_paths:
        item = copy_path(src_root, bundle_root, rel)
        if item is not None:
            copied.append(item)

    rc, git_hash = run("git rev-parse HEAD")
    if rc != 0:
        git_hash = "unknown"
    rc2, git_branch = run("git rev-parse --abbrev-ref HEAD")
    if rc2 != 0:
        git_branch = "unknown"

    file_rows: list[dict[str, Any]] = []
    for f in iter_files(bundle_root):
        rel = str(f.relative_to(bundle_root))
        file_rows.append(
            {
                "path": rel,
                "bytes": f.stat().st_size,
                "sha256": sha256(f),
            }
        )

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_name": bundle_name,
        "source_root": str(src_root),
        "git": {"branch": git_branch, "commit": git_hash},
        "options": {
            "include_logs": args.include_logs,
            "include_clean_data": args.include_clean_data,
            "archive": args.archive,
        },
        "copied_roots": copied,
        "files": file_rows,
        "file_count": len(file_rows),
        "total_bytes": sum(int(x["bytes"]) for x in file_rows),
    }

    key_artifacts = [
        "reports/thesis_assets/thesis_ready_summary.md",
        "reports/thesis_assets/thesis_ready_summary.json",
        "reports/thesis_assets/figures/figure_manifest.json",
        "reports/thesis_assets/tables/main_results_real.csv",
        "reports/thesis_assets/tables/main_results_proxy.csv",
        "reports/thesis_assets/tables/main_results_dual_view.md",
        "reports/thesis_assets/tables/baseline_audit_table.csv",
        "reports/thesis_assets/tables/dpo_beta_ablation.csv",
        "reports/thesis_assets/cases/error_cases_top30.jsonl",
        "reports/detection_predictions.jsonl",
        "reports/eval_default.md",
        "reports/sota_compare.md",
        "reports/error_analysis.md",
        "reports/gpu_experiment_closure.json",
        "reports/opening_alignment_audit.json",
    ]
    key_rows: list[dict[str, Any]] = []
    for rel in key_artifacts:
        p = bundle_root / rel
        if not p.exists():
            continue
        row: dict[str, Any] = {
            "path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
        }
        lc = line_count_jsonl(p)
        if lc is not None:
            row["jsonl_rows"] = lc
        key_rows.append(row)
    manifest["key_artifacts"] = key_rows
    (bundle_root / "bundle_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    index_csv = bundle_root / "artifact_index.csv"
    with index_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        for row in file_rows:
            writer.writerow(row)

    key_csv = bundle_root / "key_artifacts.csv"
    with key_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["path", "bytes", "sha256", "jsonl_rows"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in key_rows:
            writer.writerow({k: row.get(k) for k in fieldnames})

    readme = [
        "# Thesis Bundle",
        "",
        f"- Generated(UTC): {manifest['generated_at_utc']}",
        f"- Source commit: {git_hash}",
        f"- Source branch: {git_branch}",
        f"- File count: {manifest['file_count']}",
        f"- Total bytes: {manifest['total_bytes']}",
        "",
        "## Key Outputs",
        "- reports/thesis_assets/",
        "- reports/training/",
        "- reports/eval_default.md",
        "- reports/sota_compare.md",
        "- reports/error_analysis.md",
        "- artifact_index.csv",
        "- key_artifacts.csv",
        "- bundle_manifest.json",
        "",
        "## Verification",
        "Use `artifact_index.csv` or `bundle_manifest.json` sha256 fields to validate files after transfer.",
    ]
    (bundle_root / "README_BUNDLE.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    archive_path = out_base / f"{bundle_name}.tar.gz"
    if args.archive:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(bundle_root, arcname=bundle_name)

    output = {
        "bundle_dir": str(bundle_root),
        "archive": str(archive_path) if args.archive else None,
        "file_count": manifest["file_count"],
        "total_bytes": manifest["total_bytes"],
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
