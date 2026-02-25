#!/usr/bin/env python3
"""Lightweight SFT baseline trainer (offline simulation)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from .utils import load_jsonl, safe_mean, save_json
except ImportError:  # pragma: no cover
    from utils import load_jsonl, safe_mean, save_json


def main() -> int:
    parser = argparse.ArgumentParser(description="SFT baseline trainer")
    parser.add_argument("--train-file", default="data/clean/sft_train.jsonl")
    parser.add_argument("--dev-file", default="data/clean/sft_dev.jsonl")
    parser.add_argument("--output-dir", default="checkpoints/sft-baseline")
    parser.add_argument("--report", default="reports/sft_baseline.md")
    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="sft")
    args = parser.parse_args()

    train_rows = load_jsonl(args.train_file)
    dev_rows = load_jsonl(args.dev_file) if Path(args.dev_file).exists() else []

    avg_query_len = safe_mean([len(str(x.get("query", ""))) for x in train_rows])
    avg_answer_len = safe_mean([len(str(x.get("answer", ""))) for x in train_rows])

    # A lightweight proxy metric for baseline factual quality.
    baseline_fact_proxy = max(0.0, min(1.0, 0.35 + min(avg_answer_len / 600.0, 0.35)))

    checkpoint_dir = Path(args.output_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    model_meta = {
        "model_type": "mock_sft",
        "task": args.task,
        "train_samples": len(train_rows),
        "dev_samples": len(dev_rows),
        "avg_query_len": round(avg_query_len, 4),
        "avg_answer_len": round(avg_answer_len, 4),
        "baseline_fact_proxy": round(baseline_fact_proxy, 6),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": args.config or None,
    }
    save_json(checkpoint_dir / "metadata.json", model_meta)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = [
        "# SFT 基线训练报告（模拟）",
        "",
        "- 说明：本报告为离线代理指标统计，不代表真实参数微调训练结果。",
        f"- 训练样本数: {len(train_rows)}",
        f"- 验证样本数: {len(dev_rows)}",
        f"- 平均问题长度: {avg_query_len:.2f}",
        f"- 平均回答长度: {avg_answer_len:.2f}",
        f"- 基线事实性代理分数: {baseline_fact_proxy:.4f}",
        f"- Checkpoint: `{checkpoint_dir}/metadata.json`",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"[sft] train={len(train_rows)} dev={len(dev_rows)} checkpoint={checkpoint_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
