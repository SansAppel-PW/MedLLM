from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_build_dpo_ablation_report(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    train_dir = tmp_path / "reports/training"
    write_json(
        train_dir / "small_real_dpo_ablation_beta005_metrics.json",
        {
            "pair_count": 4,
            "steps": 8,
            "train_loss": 0.69,
            "pref_accuracy_before": 0.25,
            "pref_accuracy_after": 0.5,
            "pref_accuracy_gain": 0.25,
        },
    )
    write_json(
        train_dir / "small_real_dpo_ablation_beta020_metrics.json",
        {
            "pair_count": 4,
            "steps": 8,
            "train_loss": 0.70,
            "pref_accuracy_before": 0.25,
            "pref_accuracy_after": 0.45,
            "pref_accuracy_gain": 0.20,
        },
    )

    out_csv = tmp_path / "reports/thesis_assets/tables/dpo_beta_ablation.csv"
    out_json = tmp_path / "reports/thesis_assets/tables/dpo_beta_ablation.json"
    out_md = tmp_path / "reports/dpo_beta_ablation.md"
    cmd = [
        sys.executable,
        "scripts/audit/build_dpo_ablation_report.py",
        "--root",
        str(tmp_path),
        "--out-csv",
        str(out_csv.relative_to(tmp_path)),
        "--out-json",
        str(out_json.relative_to(tmp_path)),
        "--out-md",
        str(out_md.relative_to(tmp_path)),
    ]
    subprocess.run(cmd, cwd=repo, check=True)

    csv_text = out_csv.read_text(encoding="utf-8")
    assert "small_real_dpo_ablation_beta005" in csv_text
    assert "small_real_dpo_ablation_beta020" in csv_text
    md_text = out_md.read_text(encoding="utf-8")
    assert "最优 beta" in md_text
