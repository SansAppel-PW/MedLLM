#!/usr/bin/env python3
"""Build thesis-ready figures (PNG/PDF) from existing experiment CSV artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return None


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_image_both(image: Image.Image, png_path: Path, pdf_path: Path) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(png_path, format="PNG")
    image.save(pdf_path, format="PDF")


def find_latest_loss_csv(root: Path) -> Path | None:
    candidates: list[Path] = []
    candidates.extend((root / "reports/small_real").glob("small_real_lora_v*/loss_curve.csv"))
    direct = root / "reports/small_real/loss_curve.csv"
    if direct.exists():
        candidates.append(direct)
    candidates = [p for p in candidates if p.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def try_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_name in ("Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:  # noqa: BLE001
            continue
    return ImageFont.load_default()


def shorten_label(text: str, limit: int = 18) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def draw_line_chart(
    title: str,
    x_label: str,
    y_label: str,
    series: list[dict[str, Any]],
    out_png: Path,
    out_pdf: Path,
) -> bool:
    all_points: list[tuple[float, float]] = []
    for item in series:
        pts = item.get("points", [])
        for x, y in pts:
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                all_points.append((float(x), float(y)))
    if not all_points:
        return False

    width, height = 1080, 680
    pad_l, pad_r, pad_t, pad_b = 90, 40, 70, 90
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    x_min = min(p[0] for p in all_points)
    x_max = max(p[0] for p in all_points)
    y_min = min(p[1] for p in all_points)
    y_max = max(p[1] for p in all_points)
    if x_min == x_max:
        x_max += 1.0
    if y_min == y_max:
        y_max += 1.0

    def xy(xv: float, yv: float) -> tuple[int, int]:
        px = pad_l + int((xv - x_min) / (x_max - x_min) * plot_w)
        py = pad_t + int((y_max - yv) / (y_max - y_min) * plot_h)
        return px, py

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title = try_font(24)
    font_text = try_font(14)

    draw.rectangle((pad_l, pad_t, width - pad_r, height - pad_b), outline=(40, 40, 40), width=2)
    for i in range(6):
        yv = y_min + (y_max - y_min) * i / 5
        _, py = xy(x_min, yv)
        draw.line((pad_l, py, width - pad_r, py), fill=(225, 225, 225), width=1)
        draw.text((12, py - 8), f"{yv:.4f}", fill=(30, 30, 30), font=font_text)
    for i in range(6):
        xv = x_min + (x_max - x_min) * i / 5
        px, _ = xy(xv, y_min)
        draw.line((px, pad_t, px, height - pad_b), fill=(235, 235, 235), width=1)
        draw.text((px - 16, height - pad_b + 10), f"{xv:.2f}", fill=(30, 30, 30), font=font_text)

    for item in series:
        color = item["color"]
        points = item["points"]
        if len(points) >= 2:
            draw.line([xy(float(x), float(y)) for x, y in points], fill=color, width=3)
        for x, y in points:
            px, py = xy(float(x), float(y))
            draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=color)

    draw.text((pad_l, 20), title, fill=(10, 10, 10), font=font_title)
    draw.text((width // 2 - 40, height - 40), x_label, fill=(25, 25, 25), font=font_text)
    draw.text((20, pad_t - 30), y_label, fill=(25, 25, 25), font=font_text)

    legend_x = width - pad_r - 260
    legend_y = 20
    for idx, item in enumerate(series):
        yy = legend_y + idx * 24
        draw.line((legend_x, yy + 8, legend_x + 30, yy + 8), fill=item["color"], width=3)
        draw.text((legend_x + 40, yy), item["name"], fill=(30, 30, 30), font=font_text)

    save_image_both(image, out_png, out_pdf)
    return True


def draw_bar_chart(
    title: str,
    y_label: str,
    labels: list[str],
    values: list[float],
    out_png: Path,
    out_pdf: Path,
    bar_color: tuple[int, int, int] = (47, 114, 199),
) -> bool:
    if not labels or not values or len(labels) != len(values):
        return False
    if all(v is None for v in values):
        return False

    width, height = 1080, 680
    pad_l, pad_r, pad_t, pad_b = 90, 40, 70, 120
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    max_v = max(float(v) for v in values)
    if max_v <= 0:
        max_v = 1.0

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title = try_font(24)
    font_text = try_font(14)

    draw.rectangle((pad_l, pad_t, width - pad_r, height - pad_b), outline=(40, 40, 40), width=2)
    for i in range(6):
        yv = max_v * i / 5
        py = height - pad_b - int((yv / max_v) * plot_h)
        draw.line((pad_l, py, width - pad_r, py), fill=(230, 230, 230), width=1)
        draw.text((12, py - 8), f"{yv:.3f}", fill=(30, 30, 30), font=font_text)

    n = len(labels)
    bar_gap = 18
    bar_w = max(24, int((plot_w - bar_gap * (n + 1)) / n))
    for i, (label, value) in enumerate(zip(labels, values)):
        x0 = pad_l + bar_gap + i * (bar_w + bar_gap)
        x1 = x0 + bar_w
        h = int((float(value) / max_v) * plot_h)
        y0 = height - pad_b - h
        y1 = height - pad_b
        draw.rectangle((x0, y0, x1, y1), fill=bar_color, outline=(30, 30, 30), width=1)
        draw.text((x0 - 6, y0 - 20), f"{float(value):.4f}", fill=(20, 20, 20), font=font_text)
        draw.text((x0 - 10, y1 + 8), shorten_label(label, 14), fill=(20, 20, 20), font=font_text)

    draw.text((pad_l, 20), title, fill=(10, 10, 10), font=font_title)
    draw.text((20, pad_t - 30), y_label, fill=(25, 25, 25), font=font_text)
    save_image_both(image, out_png, out_pdf)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build thesis chart assets")
    parser.add_argument("--root", default=".")
    parser.add_argument("--loss-csv", default=None)
    parser.add_argument("--main-real-csv", default="reports/thesis_assets/tables/main_results_real.csv")
    parser.add_argument("--dpo-beta-csv", default="reports/thesis_assets/tables/dpo_beta_ablation.csv")
    parser.add_argument("--conclusion-csv", default="reports/thesis_assets/tables/conclusion_status_dashboard.csv")
    parser.add_argument("--out-dir", default="reports/thesis_assets/figures")
    parser.add_argument("--manifest", default="reports/thesis_assets/figures/figure_manifest.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "figures": [],
    }

    # 1) Loss curve
    loss_csv = Path(args.loss_csv) if args.loss_csv else find_latest_loss_csv(root)
    if loss_csv and loss_csv.exists():
        loss_rows = read_csv_rows(loss_csv)
        train_pts: list[tuple[float, float]] = []
        eval_pts: list[tuple[float, float]] = []
        for row in loss_rows:
            step = to_float(row.get("step"))
            tl = to_float(row.get("train_loss"))
            el = to_float(row.get("eval_loss"))
            if step is None:
                continue
            if tl is not None:
                train_pts.append((step, tl))
            if el is not None:
                eval_pts.append((step, el))
        ok = draw_line_chart(
            title="Training Loss Curve (Latest Small-Real Run)",
            x_label="Step",
            y_label="Loss",
            series=[
                {"name": "train_loss", "color": (47, 114, 199), "points": train_pts},
                {"name": "eval_loss", "color": (237, 125, 49), "points": eval_pts},
            ],
            out_png=out_dir / "loss_curve_latest.png",
            out_pdf=out_dir / "loss_curve_latest.pdf",
        )
        manifest["figures"].append(
            {
                "name": "loss_curve_latest",
                "source": str(loss_csv.relative_to(root)),
                "png": str((out_dir / "loss_curve_latest.png").relative_to(root)),
                "pdf": str((out_dir / "loss_curve_latest.pdf").relative_to(root)),
                "status": "ok" if ok else "skipped",
                "points": len(train_pts) + len(eval_pts),
            }
        )

    # 2) Alignment real metrics bar chart
    main_real_rows = read_csv_rows(root / args.main_real_csv)
    align_labels: list[str] = []
    align_values: list[float] = []
    loss_labels: list[str] = []
    loss_values: list[float] = []
    for row in main_real_rows:
        metric = str(row.get("metric", ""))
        setting = str(row.get("setting", ""))
        value = to_float(row.get("value"))
        if value is None:
            continue
        if metric in {"pref_accuracy_after", "aligned_score"}:
            align_labels.append(setting)
            align_values.append(value)
        if metric == "train_loss":
            loss_labels.append(setting)
            loss_values.append(value)

    ok_align = draw_bar_chart(
        title="Real Alignment Metrics Comparison",
        y_label="Score",
        labels=align_labels,
        values=align_values,
        out_png=out_dir / "alignment_metrics_bar.png",
        out_pdf=out_dir / "alignment_metrics_bar.pdf",
        bar_color=(0, 138, 97),
    )
    manifest["figures"].append(
        {
            "name": "alignment_metrics_bar",
            "source": args.main_real_csv,
            "png": str((out_dir / "alignment_metrics_bar.png").relative_to(root)),
            "pdf": str((out_dir / "alignment_metrics_bar.pdf").relative_to(root)),
            "status": "ok" if ok_align else "skipped",
            "bars": len(align_labels),
        }
    )

    ok_loss = draw_bar_chart(
        title="Train Loss Comparison (Real Mainline)",
        y_label="Train Loss",
        labels=loss_labels,
        values=loss_values,
        out_png=out_dir / "train_loss_compare_bar.png",
        out_pdf=out_dir / "train_loss_compare_bar.pdf",
        bar_color=(176, 97, 0),
    )
    manifest["figures"].append(
        {
            "name": "train_loss_compare_bar",
            "source": args.main_real_csv,
            "png": str((out_dir / "train_loss_compare_bar.png").relative_to(root)),
            "pdf": str((out_dir / "train_loss_compare_bar.pdf").relative_to(root)),
            "status": "ok" if ok_loss else "skipped",
            "bars": len(loss_labels),
        }
    )

    # 3) DPO beta ablation line chart
    dpo_rows = read_csv_rows(root / args.dpo_beta_csv)
    beta_points: list[tuple[float, float]] = []
    for row in dpo_rows:
        beta = to_float(row.get("beta"))
        score = to_float(row.get("pref_accuracy_after"))
        if beta is None or score is None:
            continue
        beta_points.append((beta, score))
    beta_points.sort(key=lambda x: x[0])

    ok_beta = draw_line_chart(
        title="DPO Beta Ablation Curve",
        x_label="beta",
        y_label="pref_accuracy_after",
        series=[{"name": "dpo_beta", "color": (112, 48, 160), "points": beta_points}],
        out_png=out_dir / "dpo_beta_curve.png",
        out_pdf=out_dir / "dpo_beta_curve.pdf",
    )
    manifest["figures"].append(
        {
            "name": "dpo_beta_curve",
            "source": args.dpo_beta_csv,
            "png": str((out_dir / "dpo_beta_curve.png").relative_to(root)),
            "pdf": str((out_dir / "dpo_beta_curve.pdf").relative_to(root)),
            "status": "ok" if ok_beta else "skipped",
            "points": len(beta_points),
        }
    )

    # 4) Conclusion status bar
    status_rows = read_csv_rows(root / args.conclusion_csv)
    counts = {"PASS": 0.0, "PARTIAL": 0.0, "FAIL": 0.0}
    for row in status_rows:
        status = str(row.get("status", "")).strip().upper()
        if status in counts:
            counts[status] += 1.0
    ok_status = draw_bar_chart(
        title="Conclusion Readiness Status Distribution",
        y_label="Count",
        labels=["PASS", "PARTIAL", "FAIL"],
        values=[counts["PASS"], counts["PARTIAL"], counts["FAIL"]],
        out_png=out_dir / "conclusion_status_bar.png",
        out_pdf=out_dir / "conclusion_status_bar.pdf",
        bar_color=(31, 119, 180),
    )
    manifest["figures"].append(
        {
            "name": "conclusion_status_bar",
            "source": args.conclusion_csv,
            "png": str((out_dir / "conclusion_status_bar.png").relative_to(root)),
            "pdf": str((out_dir / "conclusion_status_bar.pdf").relative_to(root)),
            "status": "ok" if ok_status else "skipped",
            "counts": counts,
        }
    )

    manifest_path = root / args.manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path.relative_to(root)), "figures": len(manifest["figures"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
