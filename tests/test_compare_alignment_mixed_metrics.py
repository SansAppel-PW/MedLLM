from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_compare_alignment_supports_real_and_proxy(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    dpo = tmp_path / "dpo_real.json"
    simpo = tmp_path / "simpo_proxy.json"
    kto = tmp_path / "kto_proxy.json"
    out = tmp_path / "alignment_report.md"

    write_json(
        dpo,
        {
            "method": "DPO",
            "simulation": False,
            "pair_count": 8,
            "pref_accuracy_after": 0.75,
            "pref_accuracy_gain": 0.12,
        },
    )
    write_json(
        simpo,
        {
            "method": "SimPO",
            "simulation": True,
            "samples": 8,
            "aligned_score": 0.61,
            "score_gain": 0.03,
        },
    )
    write_json(
        kto,
        {
            "method": "KTO",
            "simulation": True,
            "samples": 8,
            "aligned_score": 0.59,
            "score_gain": 0.01,
        },
    )

    cmd = [
        sys.executable,
        "src/train/compare_alignment.py",
        "--dpo",
        str(dpo),
        "--simpo",
        str(simpo),
        "--kto",
        str(kto),
        "--output",
        str(out),
    ]
    subprocess.run(cmd, cwd=repo, check=True)

    text = out.read_text(encoding="utf-8")
    assert "| DPO | real |" in text
    assert "| SimPO | proxy |" in text
    assert "当前最佳方法: **DPO**" in text
