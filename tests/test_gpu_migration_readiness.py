from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def test_gpu_migration_readiness_ready_when_only_a10_partial(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]

    write_json(
        tmp_path / "reports/opening_alignment_audit.json",
        {
            "summary": {"total": 11, "pass": 10, "partial": 1, "fail": 0},
            "checks": [
                {"id": "A05", "status": "PASS"},
                {"id": "A10", "status": "PARTIAL", "detail": "need gpu"},
            ],
        },
    )

    for rel in [
        "scripts/train/run_gpu_thesis_mainline.sh",
        "scripts/train/run_layer_b_qwen_autofallback.sh",
        "scripts/train/run_real_alignment_pipeline.sh",
        "scripts/eval/run_thesis_pipeline.sh",
        "scripts/audit/verify_gpu_experiment_closure.py",
        "scripts/audit/check_opening_alignment.py",
        "scripts/audit/build_thesis_ready_package.py",
    ]:
        touch(tmp_path / rel)

    write_json(tmp_path / "reports/training/dpo_real_metrics.json", {"simulation": False})
    write_json(tmp_path / "reports/training/simpo_metrics.json", {"simulation": False})
    write_json(tmp_path / "reports/training/kto_metrics.json", {"simulation": False})

    cmd = [
        sys.executable,
        str(repo / "scripts/audit/check_gpu_migration_readiness.py"),
        "--root",
        str(tmp_path),
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    payload = json.loads((tmp_path / "reports/gpu_migration_readiness.json").read_text(encoding="utf-8"))
    assert payload["ready_for_gpu_run"] is True
    assert payload["status"] == "READY_FOR_GPU_MAINLINE"
    assert payload["remaining_primary_gap"] == "A10"

