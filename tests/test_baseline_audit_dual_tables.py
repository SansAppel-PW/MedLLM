from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_baseline_audit_dual_outputs(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    (tmp_path / "reports/small_real/small_real_lora_v99").mkdir(parents=True, exist_ok=True)
    (tmp_path / "reports/small_real/small_real_lora_v99/eval_metrics.json").write_text("{}", encoding="utf-8")
    (tmp_path / "reports/small_real/qwen_layer_b_blocker.md").write_text("blocked", encoding="utf-8")
    (tmp_path / "reports/sota_compare.md").write_text("proxy", encoding="utf-8")

    cmd = [
        sys.executable,
        str(repo / "scripts/audit/build_baseline_audit_table.py"),
        "--small-real-run-tag",
        "small_real_lora_v99",
        "--out-csv",
        "reports/thesis_assets/tables/baseline_audit_table.csv",
        "--out-md",
        "reports/baseline_audit_table.md",
        "--out-json",
        "reports/thesis_assets/tables/baseline_audit_table.json",
        "--out-real-csv",
        "reports/thesis_assets/tables/baseline_real_mainline.csv",
        "--out-proxy-csv",
        "reports/thesis_assets/tables/baseline_proxy_background.csv",
        "--out-dual-md",
        "reports/thesis_assets/tables/baseline_audit_dual_view.md",
    ]
    subprocess.run(cmd, cwd=tmp_path, check=True)

    real_csv = (tmp_path / "reports/thesis_assets/tables/baseline_real_mainline.csv").read_text(encoding="utf-8")
    proxy_csv = (tmp_path / "reports/thesis_assets/tables/baseline_proxy_background.csv").read_text(encoding="utf-8")
    dual_md = (tmp_path / "reports/thesis_assets/tables/baseline_audit_dual_view.md").read_text(encoding="utf-8")
    payload = json.loads((tmp_path / "reports/thesis_assets/tables/baseline_audit_table.json").read_text(encoding="utf-8"))

    assert "real-mainline" in real_csv
    assert "proxy-background" in proxy_csv
    assert "Real Mainline" in dual_md
    assert "Proxy Background" in dual_md
    assert set(payload.keys()) == {"all", "real_mainline", "proxy_background"}
    assert len(payload["real_mainline"]) > 0
    assert len(payload["proxy_background"]) > 0
