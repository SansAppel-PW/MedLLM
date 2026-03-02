from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_package_thesis_bundle_builds_manifest_and_index(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]

    (tmp_path / "reports/thesis_assets/figures").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports/thesis_assets/figures/loss_curve_latest.png").write_bytes(b"png")
    (tmp_path / "reports/thesis_assets/thesis_ready_summary.md").write_text("ok\n", encoding="utf-8")
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/EXECUTION_TASKS.md").write_text("tasks\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("readme\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("all:\n\t@echo ok\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / "configs").mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(repo / "scripts/deploy/package_thesis_bundle.py"),
        "--root",
        str(tmp_path),
        "--out-dir",
        "exports",
        "--tag",
        "testbundle",
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    bundle_dir = tmp_path / "exports/thesis_bundle_testbundle"
    assert (bundle_dir / "bundle_manifest.json").exists()
    assert (bundle_dir / "artifact_index.csv").exists()
    manifest = json.loads((bundle_dir / "bundle_manifest.json").read_text(encoding="utf-8"))
    assert manifest["bundle_name"] == "thesis_bundle_testbundle"
    assert manifest["file_count"] >= 3
