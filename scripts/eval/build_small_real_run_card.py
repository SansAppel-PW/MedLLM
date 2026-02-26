#!/usr/bin/env python3
"""Build a compact run card for small real-training experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def artifact_entry(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() and path.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build small-real run card")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--train-metrics", required=True)
    parser.add_argument("--eval-metrics", required=True)
    parser.add_argument("--loss-csv", required=True)
    parser.add_argument("--loss-png", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    train_metrics_path = Path(args.train_metrics)
    eval_metrics_path = Path(args.eval_metrics)
    loss_csv_path = Path(args.loss_csv)
    loss_png_path = Path(args.loss_png)
    predictions_path = Path(args.predictions)

    manifest = load_json(manifest_path)
    train_metrics = load_json(train_metrics_path)
    eval_metrics = load_json(eval_metrics_path)

    artifacts = {
        "manifest": artifact_entry(manifest_path),
        "train_metrics": artifact_entry(train_metrics_path),
        "eval_metrics": artifact_entry(eval_metrics_path),
        "loss_csv": artifact_entry(loss_csv_path),
        "loss_png": artifact_entry(loss_png_path),
        "predictions": artifact_entry(predictions_path),
    }

    run_card = {
        "experiment": "small_real_lora",
        "task": manifest.get("task"),
        "git_commit": manifest.get("git_commit"),
        "model_name": manifest.get("model_name"),
        "tokenizer_name": manifest.get("tokenizer_name"),
        "seed": manifest.get("seed"),
        "config": manifest.get("config"),
        "local_files_only": manifest.get("local_files_only"),
        "train_file": manifest.get("train_file"),
        "train_file_sha256": manifest.get("train_file_sha256"),
        "dev_file": manifest.get("dev_file"),
        "dev_file_sha256": manifest.get("dev_file_sha256"),
        "train_samples": manifest.get("train_samples"),
        "dev_samples": manifest.get("dev_samples"),
        "framework_versions": manifest.get("framework_versions", {}),
        "cuda": manifest.get("cuda", {}),
        "environment_snapshot": manifest.get("environment_snapshot", {}),
        "train_metrics": train_metrics,
        "eval_metrics": eval_metrics,
        "artifacts": artifacts,
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(run_card, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Small Real Run Card",
        "",
        f"- task: `{run_card['task']}`",
        f"- git_commit: `{run_card['git_commit']}`",
        f"- model_name: `{run_card['model_name']}`",
        f"- seed: `{run_card['seed']}`",
        f"- config: `{run_card['config']}`",
        f"- train_samples/dev_samples: {run_card['train_samples']} / {run_card['dev_samples']}",
        "",
        "## Train Metrics",
        f"- train_loss: {train_metrics.get('train_loss')}",
        f"- final_eval_loss: {train_metrics.get('final_eval_loss')}",
        "",
        "## Eval Metrics",
        f"- exact_match: {eval_metrics.get('exact_match')}",
        f"- rouge_l_f1: {eval_metrics.get('rouge_l_f1')}",
        f"- char_f1: {eval_metrics.get('char_f1')}",
        "",
        "## Artifacts",
        f"- manifest: `{args.manifest}`",
        f"- train_metrics: `{args.train_metrics}`",
        f"- eval_metrics: `{args.eval_metrics}`",
        f"- loss_curve: `{args.loss_png}`",
        f"- predictions: `{args.predictions}`",
    ]
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[run-card] json={out_json} md={out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
