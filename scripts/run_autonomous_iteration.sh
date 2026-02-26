#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
RUN_TAG="${RUN_TAG:-small_real_lora_v3}"

echo "[loop] repo guard (preadd)"
python3 scripts/repo_guard.py --mode preadd --max-size-mb 10

echo "[loop] bootstrap minimal data assets"
"${PYTHON_BIN}" scripts/data/bootstrap_minimal_assets.py

echo "[loop] small real pipeline"
RUN_TAG="${RUN_TAG}" bash scripts/train/run_small_real_pipeline.sh || {
  echo "[loop] small-real failed; continue to build non-training artifacts"
}

echo "[loop] qwen layer-b (autofallback/blocker)"
bash scripts/train/run_layer_b_qwen_autofallback.sh || {
  echo "[loop] qwen layer-b failed (non-recoverable this round)"
}

echo "[loop] baseline audit table"
"${PYTHON_BIN}" scripts/audit/build_baseline_audit_table.py --small-real-run-tag "${RUN_TAG}"

echo "[loop] iteration report"
"${PYTHON_BIN}" scripts/audit/build_iteration_report.py --run-tag "${RUN_TAG}"

echo "[loop] thesis ready package"
"${PYTHON_BIN}" scripts/audit/build_thesis_ready_package.py

echo "[loop] done"
