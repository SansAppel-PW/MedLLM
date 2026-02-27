from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_real_alignment_methods_go_to_real_table(tmp_path: Path) -> None:
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
        tmp_path / "reports/training/dpo_real_metrics.json",
        {"simulation": False, "pair_count": 288, "pref_accuracy_after": 0.37},
    )
    write_json(
        tmp_path / "reports/training/simpo_metrics.json",
        {"simulation": False, "pair_count": 288, "pref_accuracy_after": 0.41},
    )
    write_json(
        tmp_path / "reports/training/kto_metrics.json",
        {"simulation": False, "pair_count": 288, "pref_accuracy_after": 0.35},
    )

    cmd = [
        sys.executable,
        str(repo / "scripts/audit/build_thesis_ready_package.py"),
        "--root",
        str(tmp_path),
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    main_real = (tmp_path / "reports/thesis_assets/tables/main_results_real.csv").read_text(encoding="utf-8")
    main_proxy = (tmp_path / "reports/thesis_assets/tables/main_results_proxy.csv").read_text(encoding="utf-8")
    assert "SimPO (real)" in main_real
    assert "KTO (real)" in main_real
    assert "SimPO (proxy)" not in main_proxy
    assert "KTO (proxy)" not in main_proxy

