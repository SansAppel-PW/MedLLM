#!/usr/bin/env python3
"""Build reproducible handoff manifest for GPU rental environment."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


CRITICAL_FILES = [
    "requirements.txt",
    "Makefile",
    "README.md",
    "day1_run.sh",
    "docs/GPU_MIGRATION_RUNBOOK.md",
    "docs/USAGE_MANUAL_FULL.md",
    "docs/RESOURCE_AWARE_EXECUTION.md",
    "scripts/migration/bootstrap_gpu_env.sh",
    "scripts/migration/run_gpu_thesis_experiment.sh",
    "scripts/migration/check_handoff_readiness.py",
    "scripts/migration/check_gpu_completion.py",
    "scripts/train/run_real_alignment_pipeline.sh",
    "scripts/train/run_layer_b_real_sft.sh",
    "scripts/eval/run_thesis_pipeline.sh",
    "scripts/eval/analyze_llm_fallback_impact.py",
    "scripts/pipeline/run_paper_ready.sh",
    "configs/train/sft_layer_b_real.yaml",
    "configs/train/dpo_real.yaml",
    "configs/train/simpo_real.yaml",
    "configs/train/kto_real.yaml",
]


def run_git(args: list[str]) -> str:
    out = subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)
    return out.decode("utf-8").strip()


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(rel_path: str) -> dict[str, Any]:
    abs_path = ROOT / rel_path
    if not abs_path.exists():
        return {"path": rel_path, "exists": False}
    return {
        "path": rel_path,
        "exists": True,
        "size_bytes": abs_path.stat().st_size,
        "sha256": sha256_of(abs_path),
    }


def build_manifest(model_name: str, model_tier: str) -> dict[str, Any]:
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    commit = run_git(["rev-parse", "HEAD"])
    status = run_git(["status", "--short"])

    commands = {
        "bootstrap": "bash scripts/migration/bootstrap_gpu_env.sh",
        "run_experiment": (
            f"MODEL_NAME='{model_name}' MODEL_TIER='{model_tier}' "
            "bash scripts/migration/run_gpu_thesis_experiment.sh"
        ),
        "strict_completion_check": "python3 scripts/migration/check_gpu_completion.py",
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(ROOT),
        "git": {
            "branch": branch,
            "commit": commit,
            "worktree_clean": status == "",
        },
        "target": {
            "model_name": model_name,
            "model_tier": model_tier,
            "alignment_mode": "real",
            "allow_skip_training": False,
        },
        "required_env_keys": ["OPENAI_BASE_URL", "OPENAI_API_KEY"],
        "commands": commands,
        "critical_files": [file_record(p) for p in CRITICAL_FILES],
    }


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    git = manifest["git"]
    target = manifest["target"]
    lines = [
        "# GPU Migration Handoff Manifest",
        "",
        f"- Generated at (UTC): {manifest['generated_at_utc']}",
        f"- Branch: `{git['branch']}`",
        f"- Commit: `{git['commit']}`",
        f"- Worktree clean: `{git['worktree_clean']}`",
        "",
        "## Target Run",
        f"- Model: `{target['model_name']}`",
        f"- Tier: `{target['model_tier']}`",
        "- Alignment mode: `real`",
        "- Allow skip training: `false`",
        "",
        "## Required Env",
        "- `OPENAI_BASE_URL`",
        "- `OPENAI_API_KEY`",
        "",
        "## Commands",
        f"1. `{manifest['commands']['bootstrap']}`",
        f"2. `{manifest['commands']['run_experiment']}`",
        f"3. `{manifest['commands']['strict_completion_check']}`",
        "",
        "## Critical Files",
        "| path | exists | size_bytes | sha256 |",
        "|---|---|---:|---|",
    ]
    for item in manifest["critical_files"]:
        lines.append(
            f"| {item['path']} | {item.get('exists', False)} | {item.get('size_bytes', 0)} | {item.get('sha256', '')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build GPU handoff manifest")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--model-tier", default="7b")
    parser.add_argument("--json-out", default="reports/migration/gpu_handoff_manifest.json")
    parser.add_argument("--md-out", default="reports/migration/gpu_handoff_manifest.md")
    args = parser.parse_args()

    payload = build_manifest(model_name=args.model_name, model_tier=args.model_tier)

    json_path = ROOT / args.json_out
    md_path = ROOT / args.md_out
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(md_path, payload)

    print(json.dumps({"json": args.json_out, "md": args.md_out, "commit": payload["git"]["commit"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
