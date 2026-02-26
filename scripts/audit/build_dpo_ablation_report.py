#!/usr/bin/env python3
"""Build DPO beta-ablation report from real training metrics."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_beta(run_tag: str) -> float | None:
    m = re.search(r"beta(\d+)$", run_tag)
    if not m:
        return None
    raw = m.group(1)
    if len(raw) <= 1:
        return float(raw)
    return float(f"{raw[0]}.{raw[1:]}")


def collect_rows(root: Path) -> list[dict[str, Any]]:
    train_dir = root / "reports/training"
    rows: list[dict[str, Any]] = []
    for p in train_dir.glob("small_real_dpo_ablation_beta*_metrics.json"):
        data = load_json(p)
        run_tag = p.stem.replace("_metrics", "")
        rows.append(
            {
                "run_tag": run_tag,
                "beta": parse_beta(run_tag),
                "pair_count": data.get("pair_count"),
                "steps": data.get("steps"),
                "train_loss": data.get("train_loss"),
                "pref_accuracy_before": data.get("pref_accuracy_before"),
                "pref_accuracy_after": data.get("pref_accuracy_after"),
                "pref_accuracy_gain": data.get("pref_accuracy_gain"),
                "metrics_path": str(p.relative_to(root)),
            }
        )
    rows.sort(key=lambda x: (x.get("beta") is None, x.get("beta")))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Build DPO ablation report")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-csv", default="reports/thesis_assets/tables/dpo_beta_ablation.csv")
    parser.add_argument("--out-json", default="reports/thesis_assets/tables/dpo_beta_ablation.json")
    parser.add_argument("--out-md", default="reports/dpo_beta_ablation.md")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rows = collect_rows(root)

    fields = [
        "run_tag",
        "beta",
        "pair_count",
        "steps",
        "train_loss",
        "pref_accuracy_before",
        "pref_accuracy_after",
        "pref_accuracy_gain",
        "metrics_path",
    ]
    write_csv(root / args.out_csv, rows, fields)
    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    best = None
    if rows:
        best = max(rows, key=lambda x: float(x.get("pref_accuracy_after") or 0.0))

    lines = [
        "# DPO Beta 消融报告（Small-Real）",
        "",
        f"- 运行数: {len(rows)}",
        f"- CSV: `{args.out_csv}`",
        f"- JSON: `{args.out_json}`",
        "",
        "| run_tag | beta | pair_count | steps | train_loss | acc_before | acc_after | gain |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['run_tag']} | {r.get('beta')} | {r.get('pair_count')} | {r.get('steps')} | "
            f"{float(r.get('train_loss') or 0.0):.6f} | {float(r.get('pref_accuracy_before') or 0.0):.4f} | "
            f"{float(r.get('pref_accuracy_after') or 0.0):.4f} | {float(r.get('pref_accuracy_gain') or 0.0):.4f} |"
        )

    lines.extend(["", "## 结论"])
    if best is None:
        lines.append("- 当前无可用消融结果。")
    else:
        lines.append(
            f"- 最优 beta: `{best.get('beta')}`，pref_accuracy_after={float(best.get('pref_accuracy_after') or 0.0):.4f}。"
        )
        if int(best.get("pair_count") or 0) < 20:
            lines.append("- 注意：当前样本数较小（<20），仅作流程验证，不可作为论文主结论。")

    out_md = root / args.out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[dpo-ablation-report] rows={len(rows)} csv={args.out_csv} md={args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
