from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_interface_consistency_passes(tmp_path: Path) -> None:
    out_json = tmp_path / "interface_consistency.json"
    out_md = tmp_path / "interface_consistency.md"

    subprocess.run(
        [
            sys.executable,
            "scripts/audit/check_pipeline_interface_consistency.py",
            "--root",
            str(REPO_ROOT),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ],
        cwd=REPO_ROOT,
        check=True,
    )

    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["pass"] >= 1
    assert out_md.exists()
