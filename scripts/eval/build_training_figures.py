#!/usr/bin/env python3
"""Build training loss figures and summary tables for thesis assets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def extract_step_loss(rows: list[dict[str, Any]]) -> tuple[list[int], list[float]]:
    steps: list[int] = []
    losses: list[float] = []
    for row in rows:
        if "step" not in row or "loss" not in row:
            continue
        try:
            step = int(row["step"])
            loss = float(row["loss"])
        except (TypeError, ValueError):
            continue
        steps.append(step)
        losses.append(loss)
    return steps, losses


def save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["name", "points", "min_loss", "max_loss", "final_loss", "final_step", "source_log", "figure"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_note(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build training loss figures")
    parser.add_argument("--out-dir", default="reports/thesis_assets/figures")
    parser.add_argument("--summary-csv", default="reports/thesis_assets/tables/training_loss_summary.csv")
    parser.add_argument(
        "--logs",
        default=(
            "logs/layer_b/qwen25_7b_sft/train_log.jsonl,"
            "logs/dpo-real-baseline/train_log.jsonl,"
            "logs/simpo-real-baseline/train_log.jsonl,"
            "logs/kto-real-baseline/train_log.jsonl"
        ),
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:  # noqa: BLE001
        write_note(
            out_dir / "training_loss_note.md",
            "# Training Loss Figures\n\n未安装 matplotlib，无法自动生成训练曲线图。\n",
        )
        save_csv(Path(args.summary_csv), [])
        print(json.dumps({"figures": 0, "note": "matplotlib_missing"}, ensure_ascii=False))
        return 0

    summary_rows: list[dict[str, Any]] = []
    generated = 0

    log_paths = [Path(x.strip()) for x in args.logs.split(",") if x.strip()]
    for log_path in log_paths:
        rows = load_jsonl(log_path)
        steps, losses = extract_step_loss(rows)
        if not steps:
            continue
        name = log_path.parent.name
        fig_name = f"training_loss_{name}.png"
        fig_path = out_dir / fig_name

        plt.figure(figsize=(7.2, 4.0))
        plt.plot(steps, losses, linewidth=1.8, marker="o", markersize=3)
        plt.title(f"Training Loss - {name}")
        plt.xlabel("Step")
        plt.ylabel("Loss")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(fig_path, dpi=160)
        plt.close()

        summary_rows.append(
            {
                "name": name,
                "points": len(steps),
                "min_loss": min(losses),
                "max_loss": max(losses),
                "final_loss": losses[-1],
                "final_step": steps[-1],
                "source_log": str(log_path),
                "figure": str(fig_path),
            }
        )
        generated += 1

    save_csv(Path(args.summary_csv), summary_rows)
    if generated == 0:
        write_note(
            out_dir / "training_loss_note.md",
            "# Training Loss Figures\n\n未发现可用训练日志（train_log.jsonl），暂无可绘制曲线。\n",
        )

    print(json.dumps({"figures": generated, "summary": args.summary_csv}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
