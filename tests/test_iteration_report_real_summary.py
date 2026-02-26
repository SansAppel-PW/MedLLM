from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_iteration_report_includes_real_data_and_alignment(tmp_path: Path) -> None:
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
        tmp_path / "reports/real_dataset_summary.json",
        {"train_count": 288, "dev_count": 36, "test_count": 36, "benchmark_count": 200},
    )
    write_json(
        tmp_path / "reports/training/dpo_real_metrics.json",
        {"pair_count": 288, "pref_accuracy_after": 0.37},
    )
    write_json(
        tmp_path / "reports/training/simpo_metrics.json",
        {"aligned_score": 0.81},
    )
    write_json(
        tmp_path / "reports/training/kto_metrics.json",
        {"aligned_score": 0.58},
    )
    (tmp_path / "reports/thesis_assets/tables").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports/thesis_assets/tables/baseline_audit_table.csv").write_text("h\n", encoding="utf-8")

    out_md = tmp_path / "reports/iteration/latest_iteration_report.md"
    out_json = tmp_path / "reports/iteration/latest_iteration_report.json"
    cmd = [
        sys.executable,
        str(repo / "scripts/audit/build_iteration_report.py"),
        "--run-tag",
        "small_real_lora_v99",
        "--small-real-metrics",
        "reports/training/small_real_lora_v99_metrics.json",
        "--small-real-eval",
        "reports/small_real/small_real_lora_v99/eval_metrics.json",
        "--out-md",
        str(out_md.relative_to(tmp_path)),
        "--out-json",
        str(out_json.relative_to(tmp_path)),
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert payload["real_data_summary"]["train_count"] == 288
    assert payload["real_alignment_summary"]["dpo_pair_count"] == 288
    assert payload["real_alignment_summary"]["best_method"] == "SimPO"
    assert payload["real_alignment_summary"]["best_score"] == 0.81

    md_text = out_md.read_text(encoding="utf-8")
    assert "真实数据摘要" in md_text
    assert "真实对齐摘要" in md_text
