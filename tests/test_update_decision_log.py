from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def test_update_decision_log_append_and_dedup(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    iteration = {
        "generated_at_utc": "2026-02-26T00:00:00+00:00",
        "run_tag": "small_real_lora_v99",
        "small_real_summary": {"train_loss": 1.0},
        "real_data_summary": {"train_count": 288, "dev_count": 36, "test_count": 36},
        "real_alignment_summary": {"dpo_pair_count": 288, "best_method": "SimPO"},
        "risk_assessment": [],
        "next_min_loop": ["step-a"],
    }
    write_json(tmp_path / "reports/iteration/latest_iteration_report.json", iteration)

    cmd = [sys.executable, str(repo / "scripts/audit/update_decision_log.py")]
    subprocess.run(cmd, cwd=tmp_path, check=True)
    subprocess.run(cmd, cwd=tmp_path, check=True)

    rows = read_jsonl(tmp_path / "reports/iteration/decision_log.jsonl")
    assert len(rows) == 1
    assert rows[0]["run_tag"] == "small_real_lora_v99"

    iteration["generated_at_utc"] = "2026-02-26T01:00:00+00:00"
    write_json(tmp_path / "reports/iteration/latest_iteration_report.json", iteration)
    subprocess.run(cmd, cwd=tmp_path, check=True)

    rows = read_jsonl(tmp_path / "reports/iteration/decision_log.jsonl")
    assert len(rows) == 2
    md_text = (tmp_path / "reports/iteration/decision_log.md").read_text(encoding="utf-8")
    assert "Latest Decision" in md_text
