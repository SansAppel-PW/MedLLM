from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_verify_gpu_experiment_closure_strict_pass(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]

    write_json(tmp_path / "reports/training/layer_b_qwen25_7b_sft_metrics.json", {"train_loss": 1.1})
    write_json(
        tmp_path / "reports/training/dpo_real_metrics.json",
        {"simulation": False, "pair_count": 288, "pref_accuracy_after": 0.33},
    )
    write_json(
        tmp_path / "reports/training/simpo_metrics.json",
        {"simulation": False, "pair_count": 288, "pref_accuracy_after": 0.35},
    )
    write_json(
        tmp_path / "reports/training/kto_metrics.json",
        {"simulation": False, "pair_count": 288, "pref_accuracy_after": 0.31},
    )
    write_json(
        tmp_path / "reports/opening_alignment_audit.json",
        {"checks": [{"id": "A10", "status": "PASS"}]},
    )
    (tmp_path / "reports/thesis_assets/tables").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports/thesis_assets/tables/main_results_real.csv").write_text(
        "section,setting,method_type,metric,value\n"
        "generation,Qwen2.5-7B Layer-B,real,train_loss,1.1\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(repo / "scripts/audit/verify_gpu_experiment_closure.py"),
        "--root",
        str(tmp_path),
        "--strict",
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    payload = json.loads((tmp_path / "reports/gpu_experiment_closure.json").read_text(encoding="utf-8"))
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["pass"] == 6

