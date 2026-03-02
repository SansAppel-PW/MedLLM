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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def find_layer_b_train_log(root: Path) -> Path | None:
    direct_candidates = [
        root / "logs/layer_b/qwen25_7b_sft/train_log.jsonl",
        root / "logs/layer_b/qwen25_7b_sft/real_train_log.jsonl",
        root / "logs/layer_b/qwen25_7b_qlora_attempt1/train_log.jsonl",
        root / "logs/layer_b/qwen25_7b_qlora_attempt1/attempt.log",
    ]
    for p in direct_candidates:
        if p.exists():
            return p
    qlora_logs = sorted(
        (root / "logs/layer_b").glob("qwen25_7b_qlora_attempt*/train_log.jsonl"),
        key=lambda x: x.stat().st_mtime if x.exists() else 0.0,
        reverse=True,
    )
    for p in qlora_logs:
        if p.exists():
            return p
    qlora_attempt_logs = sorted(
        (root / "logs/layer_b").glob("qwen25_7b_qlora_attempt*/attempt.log"),
        key=lambda x: x.stat().st_mtime if x.exists() else 0.0,
        reverse=True,
    )
    for p in qlora_attempt_logs:
        if p.exists():
            return p
    return None


def parse_train_log_jsonl(path: Path) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    train_pts: list[tuple[float, float]] = []
    eval_pts: list[tuple[float, float]] = []
    if not path.exists():
        return train_pts, eval_pts
    if path.name == "attempt.log":
        step = 0.0
        eval_step = 0.0
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m_loss = re.search(r"'loss':\s*'([^']+)'", line)
                if m_loss:
                    try:
                        loss_val = float(m_loss.group(1))
                    except ValueError:
                        loss_val = None
                    if loss_val is not None:
                        step += 10.0
                        train_pts.append((step, loss_val))
                m_eval = re.search(r"'eval_loss':\s*([0-9.+-eE]+)", line)
                if m_eval:
                    try:
                        eval_val = float(m_eval.group(1))
                    except ValueError:
                        eval_val = None
                    if eval_val is not None:
                        eval_step = max(eval_step + 100.0, step)
                        eval_pts.append((eval_step, eval_val))
        return train_pts, eval_pts
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            step = to_float(row.get("step"))
            if step is None:
                continue
            loss = to_float(row.get("loss"))
            eval_loss = to_float(row.get("eval_loss"))
            if loss is not None:
                train_pts.append((step, loss))
            if eval_loss is not None:
                eval_pts.append((step, eval_loss))
    return train_pts, eval_pts


def dataset_count(summary: dict[str, Any], key: str) -> float:
    direct = summary.get(key)
    if isinstance(direct, (int, float)):
        return float(direct)
    if key in {"train_count", "dev_count", "test_count"}:
        final_sft = summary.get("final_sft")
        if isinstance(final_sft, dict) and isinstance(final_sft.get(key), (int, float)):
            return float(final_sft[key])
    if key == "benchmark_count":
        final_bench = summary.get("final_benchmark")
        if isinstance(final_bench, dict) and isinstance(final_bench.get("count"), (int, float)):
            return float(final_bench["count"])
    if key == "merged_after_dedup":
        comp = summary.get("external_real_qa_component")
        if isinstance(comp, dict) and isinstance(comp.get("raw_merged_count"), (int, float)):
            return float(comp["raw_merged_count"])
    return 0.0


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
    parser.add_argument("--dataset-summary", default="reports/real_dataset_summary.json")
    parser.add_argument("--main-real-csv", default="reports/thesis_assets/tables/main_results_real.csv")
    parser.add_argument("--dpo-beta-csv", default="reports/thesis_assets/tables/dpo_beta_ablation.csv")
    parser.add_argument("--conclusion-csv", default="reports/thesis_assets/tables/conclusion_status_dashboard.csv")
    parser.add_argument("--sota-csv", default="reports/thesis_assets/tables/sota_compare_metrics.csv")
    parser.add_argument("--confusion-csv", default="reports/thesis_assets/tables/detection_confusion.csv")
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

    # 1) Small-real loss curve
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

    # 2) Layer-B loss curve (if log exists)
    layer_b_log = find_layer_b_train_log(root)
    if layer_b_log:
        lb_train, lb_eval = parse_train_log_jsonl(layer_b_log)
        ok_layer_b = draw_line_chart(
            title="Qwen2.5-7B Layer-B Training Loss Curve",
            x_label="Step",
            y_label="Loss",
            series=[
                {"name": "train_loss", "color": (0, 102, 204), "points": lb_train},
                {"name": "eval_loss", "color": (204, 102, 0), "points": lb_eval},
            ],
            out_png=out_dir / "layer_b_loss_curve.png",
            out_pdf=out_dir / "layer_b_loss_curve.pdf",
        )
        manifest["figures"].append(
            {
                "name": "layer_b_loss_curve",
                "source": str(layer_b_log.relative_to(root)),
                "png": str((out_dir / "layer_b_loss_curve.png").relative_to(root)),
                "pdf": str((out_dir / "layer_b_loss_curve.pdf").relative_to(root)),
                "status": "ok" if ok_layer_b else "skipped",
                "points": len(lb_train) + len(lb_eval),
            }
        )

    # 3) Alignment real metrics bar chart
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

    # 4) DPO beta ablation line chart
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

    # 5) Conclusion status bar
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

    # 6) Dataset scale bar chart
    dataset_summary = load_json(root / args.dataset_summary)
    ds_labels = ["merged", "train", "dev", "test", "benchmark"]
    ds_values = [
        dataset_count(dataset_summary, "merged_after_dedup"),
        dataset_count(dataset_summary, "train_count"),
        dataset_count(dataset_summary, "dev_count"),
        dataset_count(dataset_summary, "test_count"),
        dataset_count(dataset_summary, "benchmark_count"),
    ]
    ok_dataset = draw_bar_chart(
        title="Real Dataset Scale Overview",
        y_label="Count",
        labels=ds_labels,
        values=ds_values,
        out_png=out_dir / "dataset_scale_bar.png",
        out_pdf=out_dir / "dataset_scale_bar.pdf",
        bar_color=(70, 130, 180),
    )
    manifest["figures"].append(
        {
            "name": "dataset_scale_bar",
            "source": args.dataset_summary,
            "png": str((out_dir / "dataset_scale_bar.png").relative_to(root)),
            "pdf": str((out_dir / "dataset_scale_bar.pdf").relative_to(root)),
            "status": "ok" if ok_dataset else "skipped",
            "bars": len(ds_labels),
        }
    )

    # 7) SOTA F1 comparison bar chart
    sota_rows = read_csv_rows(root / args.sota_csv)
    sota_labels: list[str] = []
    sota_f1: list[float] = []
    for row in sota_rows:
        name = str(row.get("name", "")).strip()
        f1 = to_float(row.get("f1"))
        if not name or f1 is None:
            continue
        sota_labels.append(name)
        sota_f1.append(f1)
    ok_sota = draw_bar_chart(
        title="SOTA/Proxy F1 Comparison",
        y_label="F1",
        labels=sota_labels,
        values=sota_f1,
        out_png=out_dir / "sota_f1_bar.png",
        out_pdf=out_dir / "sota_f1_bar.pdf",
        bar_color=(46, 139, 87),
    )
    manifest["figures"].append(
        {
            "name": "sota_f1_bar",
            "source": args.sota_csv,
            "png": str((out_dir / "sota_f1_bar.png").relative_to(root)),
            "pdf": str((out_dir / "sota_f1_bar.pdf").relative_to(root)),
            "status": "ok" if ok_sota else "skipped",
            "bars": len(sota_labels),
        }
    )

    # 8) Detection confusion bar chart
    confusion_rows = read_csv_rows(root / args.confusion_csv)
    c_labels: list[str] = []
    c_values: list[float] = []
    for row in confusion_rows:
        name = str(row.get("name", "")).strip()
        count = to_float(row.get("count"))
        if not name or count is None:
            continue
        c_labels.append(name)
        c_values.append(count)
    ok_conf = draw_bar_chart(
        title="Detection Confusion Matrix Counts",
        y_label="Count",
        labels=c_labels,
        values=c_values,
        out_png=out_dir / "detection_confusion_bar.png",
        out_pdf=out_dir / "detection_confusion_bar.pdf",
        bar_color=(205, 92, 92),
    )
    manifest["figures"].append(
        {
            "name": "detection_confusion_bar",
            "source": args.confusion_csv,
            "png": str((out_dir / "detection_confusion_bar.png").relative_to(root)),
            "pdf": str((out_dir / "detection_confusion_bar.pdf").relative_to(root)),
            "status": "ok" if ok_conf else "skipped",
            "bars": len(c_labels),
        }
    )

    manifest_path = root / args.manifest
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path.relative_to(root)), "figures": len(manifest["figures"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
