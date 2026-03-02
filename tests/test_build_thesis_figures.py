from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def test_build_thesis_figures_generates_png_and_pdf(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]

    write_csv(
        tmp_path / "reports/small_real/small_real_lora_v99/loss_curve.csv",
        ["step", "epoch", "train_loss", "eval_loss"],
        [
            ["1", "0.2", "2.3", "2.6"],
            ["2", "0.4", "2.1", "2.4"],
            ["3", "0.6", "1.9", "2.2"],
        ],
    )
    write_csv(
        tmp_path / "reports/thesis_assets/tables/main_results_real.csv",
        ["section", "setting", "method_type", "metric", "value", "sample_count", "evidence", "note"],
        [
            ["generation", "Qwen2.5-7B Layer-B", "real", "train_loss", "1.2", "", "m1", "n1"],
            ["generation", "LoRA Small-Real", "real", "train_loss", "2.1", "", "m2", "n2"],
            ["alignment", "DPO (real)", "real", "pref_accuracy_after", "0.91", "100", "m3", "n3"],
            ["alignment", "SimPO (real)", "real", "pref_accuracy_after", "0.92", "100", "m4", "n4"],
            ["alignment", "KTO (real)", "real", "pref_accuracy_after", "0.93", "100", "m5", "n5"],
        ],
    )
    write_csv(
        tmp_path / "reports/thesis_assets/tables/dpo_beta_ablation.csv",
        ["run_tag", "beta", "pair_count", "steps", "train_loss", "pref_accuracy_before", "pref_accuracy_after", "pref_accuracy_gain", "metrics_path"],
        [
            ["r1", "0.05", "100", "10", "0.7", "0.5", "0.8", "0.3", "p1"],
            ["r2", "0.10", "100", "10", "0.7", "0.5", "0.85", "0.35", "p2"],
            ["r3", "0.20", "100", "10", "0.7", "0.5", "0.83", "0.33", "p3"],
        ],
    )
    write_csv(
        tmp_path / "reports/thesis_assets/tables/conclusion_status_dashboard.csv",
        ["dimension", "status", "icon", "evidence", "note"],
        [
            ["A", "PASS", "[OK]", "e1", "n1"],
            ["B", "PASS", "[OK]", "e2", "n2"],
            ["C", "PARTIAL", "[WARN]", "e3", "n3"],
        ],
    )

    cmd = [
        sys.executable,
        str(repo / "scripts/eval/build_thesis_figures.py"),
        "--root",
        str(tmp_path),
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    expected_png = [
        tmp_path / "reports/thesis_assets/figures/loss_curve_latest.png",
        tmp_path / "reports/thesis_assets/figures/alignment_metrics_bar.png",
        tmp_path / "reports/thesis_assets/figures/train_loss_compare_bar.png",
        tmp_path / "reports/thesis_assets/figures/dpo_beta_curve.png",
        tmp_path / "reports/thesis_assets/figures/conclusion_status_bar.png",
    ]
    expected_pdf = [Path(str(p).replace(".png", ".pdf")) for p in expected_png]
    for p in expected_png + expected_pdf:
        assert p.exists(), f"missing figure file: {p}"

    manifest = json.loads((tmp_path / "reports/thesis_assets/figures/figure_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["figures"]) >= 4
    assert any(x["name"] == "loss_curve_latest" and x["status"] == "ok" for x in manifest["figures"])
