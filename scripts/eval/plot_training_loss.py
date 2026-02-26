#!/usr/bin/env python3
"""Export and plot training/eval loss from JSONL logs (no matplotlib dependency)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def to_float(raw: object) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot loss curve from trainer JSONL logs")
    parser.add_argument("--log-jsonl", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-png", required=True)
    parser.add_argument("--out-pdf", required=True)
    args = parser.parse_args()

    rows = []
    with Path(args.log_jsonl).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            step = int(item.get("step", 0))
            train_loss = to_float(item.get("loss"))
            eval_loss = to_float(item.get("eval_loss"))
            if train_loss is None and eval_loss is None:
                continue
            rows.append(
                {
                    "step": step,
                    "train_loss": train_loss,
                    "eval_loss": eval_loss,
                    "epoch": to_float(item.get("epoch")),
                }
            )

    rows.sort(key=lambda x: x["step"])
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.out_csv).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["step", "epoch", "train_loss", "eval_loss"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    train_points = [(r["step"], r["train_loss"]) for r in rows if r["train_loss"] is not None]
    eval_points = [(r["step"], r["eval_loss"]) for r in rows if r["eval_loss"] is not None]
    all_points = train_points + eval_points
    if not all_points:
        raise ValueError("No train/eval loss points found in log file.")

    width, height = 1000, 600
    pad_l, pad_r, pad_t, pad_b = 80, 40, 50, 70
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    x_min = min(p[0] for p in all_points)
    x_max = max(p[0] for p in all_points)
    y_min = min(p[1] for p in all_points)
    y_max = max(p[1] for p in all_points)
    if x_min == x_max:
        x_max += 1
    if y_min == y_max:
        y_max += 1e-6

    def xy(step: float, loss: float) -> tuple[int, int]:
        x = pad_l + int((step - x_min) / (x_max - x_min) * plot_w)
        y = pad_t + int((y_max - loss) / (y_max - y_min) * plot_h)
        return x, y

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("Arial.ttf", 14)
    except Exception:  # noqa: BLE001
        font = ImageFont.load_default()

    # Axes
    draw.line((pad_l, pad_t, pad_l, height - pad_b), fill="black", width=2)
    draw.line((pad_l, height - pad_b, width - pad_r, height - pad_b), fill="black", width=2)

    # Grid and ticks (5 y ticks, up to 6 x ticks)
    for i in range(6):
        y_val = y_min + (y_max - y_min) * i / 5
        _, y_pos = xy(x_min, y_val)
        draw.line((pad_l, y_pos, width - pad_r, y_pos), fill=(230, 230, 230), width=1)
        draw.text((10, y_pos - 7), f"{y_val:.4f}", fill="black", font=font)
    x_ticks = min(6, max(2, len({p[0] for p in all_points})))
    for i in range(x_ticks):
        x_val = x_min + (x_max - x_min) * i / (x_ticks - 1)
        x_pos, _ = xy(x_val, y_min)
        draw.line((x_pos, pad_t, x_pos, height - pad_b), fill=(235, 235, 235), width=1)
        draw.text((x_pos - 10, height - pad_b + 10), f"{int(round(x_val))}", fill="black", font=font)

    # Curves
    if len(train_points) >= 2:
        draw.line([xy(s, l) for s, l in train_points], fill=(47, 114, 199), width=3)
    for s, l in train_points:
        x, y = xy(s, l)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(47, 114, 199))

    if len(eval_points) >= 2:
        draw.line([xy(s, l) for s, l in eval_points], fill=(237, 125, 49), width=3)
    for s, l in eval_points:
        x, y = xy(s, l)
        draw.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(237, 125, 49))

    # Labels and legend
    draw.text((pad_l, 14), "Small Real Training Loss Curve", fill="black", font=font)
    draw.text((width // 2 - 30, height - 35), "Step", fill="black", font=font)
    draw.text((15, pad_t - 20), "Loss", fill="black", font=font)
    draw.line((width - 230, 20, width - 200, 20), fill=(47, 114, 199), width=3)
    draw.text((width - 190, 12), "train_loss", fill="black", font=font)
    draw.line((width - 230, 42, width - 200, 42), fill=(237, 125, 49), width=3)
    draw.text((width - 190, 34), "eval_loss", fill="black", font=font)

    Path(args.out_png).parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out_png, format="PNG")
    image.save(args.out_pdf, format="PDF")

    print(f"[loss-plot] rows={len(rows)} csv={args.out_csv} png={args.out_png} pdf={args.out_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
