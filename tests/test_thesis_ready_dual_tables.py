from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_build_thesis_ready_dual_tables(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]

    write_json(
        tmp_path / "reports/training/small_real_lora_v99_metrics.json",
        {"train_loss": 1.2, "final_eval_loss": 1.1},
    )
    write_json(
        tmp_path / "reports/small_real/small_real_lora_v99/eval_metrics.json",
        {"exact_match": 0.2, "rouge_l_f1": 0.3, "char_f1": 0.4},
    )
    write_json(
        tmp_path / "reports/small_real/base_model_eval_metrics.json",
        {"samples": 8, "exact_match": 0.1, "rouge_l_f1": 0.12, "char_f1": 0.2},
    )
    write_json(
        tmp_path / "reports/training/dpo_real_metrics.json",
        {"pair_count": 288, "pref_accuracy_after": 0.37},
    )
    write_json(
        tmp_path / "reports/training/dpo_metrics.json",
        {"samples": 100, "aligned_score": 0.78},
    )
    write_json(
        tmp_path / "reports/training/simpo_metrics.json",
        {"samples": 100, "aligned_score": 0.81},
    )
    write_json(
        tmp_path / "reports/training/kto_metrics.json",
        {"samples": 100, "aligned_score": 0.58},
    )

    out_md = tmp_path / "reports/thesis_assets/thesis_ready_summary.md"
    out_json = tmp_path / "reports/thesis_assets/thesis_ready_summary.json"
    cmd = [
        sys.executable,
        str(repo / "scripts/audit/build_thesis_ready_package.py"),
        "--root",
        str(tmp_path),
        "--out-md",
        str(out_md.relative_to(tmp_path)),
        "--out-json",
        str(out_json.relative_to(tmp_path)),
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    main_real = (tmp_path / "reports/thesis_assets/tables/main_results_real.csv").read_text(encoding="utf-8")
    main_proxy = (tmp_path / "reports/thesis_assets/tables/main_results_proxy.csv").read_text(encoding="utf-8")
    dual_md = (tmp_path / "reports/thesis_assets/tables/main_results_dual_view.md").read_text(encoding="utf-8")
    summary = json.loads(out_json.read_text(encoding="utf-8"))

    assert "DPO (real)" in main_real
    assert "SimPO (proxy)" in main_proxy
    assert "口径约束" in dual_md
    assert summary["artifacts"]["main_results_real_csv"].endswith("main_results_real.csv")
    assert summary["artifacts"]["main_results_proxy_csv"].endswith("main_results_proxy.csv")
