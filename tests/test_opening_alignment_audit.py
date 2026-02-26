from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def touch(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_opening_alignment_audit_reports_expected_summary(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]

    touch(
        tmp_path / ".gitignore",
        "\n".join([".env", "/data/", "/checkpoints/", "*.safetensors", "*.ckpt"]) + "\n",
    )
    touch(tmp_path / "scripts/repo_guard.py", "# guard\n")

    for rel in [
        "scripts/data/run_data_governance_pipeline.py",
        "scripts/train/run_small_real_pipeline.sh",
        "scripts/train/run_real_alignment_pipeline.sh",
        "scripts/eval/run_thesis_pipeline.sh",
        "scripts/run_autonomous_iteration.sh",
    ]:
        touch(tmp_path / rel, "#!/usr/bin/env bash\n")

    write_json(
        tmp_path / "reports/real_dataset_summary.json",
        {"train_count": 288, "dev_count": 36, "test_count": 36},
    )
    write_json(
        tmp_path / "reports/thesis_assets/thesis_ready_summary.json",
        {"latest_small_real_run": "small_real_lora_v99"},
    )
    write_json(
        tmp_path / "reports/training/small_real_lora_v99_metrics.json",
        {"train_loss": 1.0},
    )
    touch(tmp_path / "reports/small_real/small_real_lora_v99/loss_curve.csv", "step,loss\n1,1.0\n")
    touch(tmp_path / "reports/small_real/small_real_lora_v99/loss_curve.png", "png")
    write_json(
        tmp_path / "reports/small_real/small_real_lora_v99/run_card.json",
        {"run_tag": "small_real_lora_v99"},
    )
    write_json(
        tmp_path / "reports/training/dpo_real_metrics.json",
        {"simulation": False, "pair_count": 288},
    )
    write_json(
        tmp_path / "reports/training/simpo_metrics.json",
        {"simulation": True, "aligned_score": 0.8},
    )
    write_json(
        tmp_path / "reports/training/kto_metrics.json",
        {"simulation": True, "aligned_score": 0.6},
    )
    touch(tmp_path / "reports/alignment_compare.md", "compare")

    write_json(
        tmp_path / "reports/thesis_assets/tables/baseline_audit_table.json",
        {
            "all": [
                {"model": "Med-PaLM 2"},
                {"model": "ChatDoctor"},
                {"model": "HuatuoGPT-II"},
                {"model": "DISC-MedLLM"},
                {"model": "Qwen2.5-7B"},
            ]
        },
    )

    touch(tmp_path / "reports/eval_default.md", "FactScore\nWin Rate\nInterceptionRate\n")
    touch(tmp_path / "reports/thesis_assets/tables/main_results_real.csv", "model,rouge_l_f1\nx,0.1\n")

    touch(tmp_path / "eval/metrics.py", "def f():\n    return 1\n")
    touch(tmp_path / "scripts/eval/run_sota_compare.py", "print('offline')\n")

    for rel in [
        "reports/thesis_assets/tables/main_results_proxy.csv",
        "reports/thesis_assets/tables/main_results_dual_view.md",
        "reports/thesis_assets/tables/baseline_real_mainline.csv",
        "reports/thesis_assets/tables/baseline_proxy_background.csv",
        "reports/thesis_assets/tables/baseline_audit_dual_view.md",
        "reports/training/layer_b_qwen25_7b_sft_metrics.json",
    ]:
        touch(tmp_path / rel, "ok\n")

    write_json(tmp_path / "reports/task_audit.json", {"summary": {"done_missing": 0}})
    touch(tmp_path / "reports/task_audit.md", "# audit\n")

    out_md = tmp_path / "reports/opening_alignment_audit.md"
    out_json = tmp_path / "reports/opening_alignment_audit.json"
    cmd = [
        sys.executable,
        str(repo / "scripts/audit/check_opening_alignment.py"),
        "--root",
        str(tmp_path),
        "--out-md",
        str(out_md.relative_to(tmp_path)),
        "--out-json",
        str(out_json.relative_to(tmp_path)),
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["partial"] == 2  # A05/A08
    assert payload["summary"]["pass"] == 9

    checks = {row["id"]: row for row in payload["checks"]}
    assert checks["A05"]["status"] == "PARTIAL"
    assert checks["A08"]["status"] == "PARTIAL"
    assert checks["A10"]["status"] == "PASS"

