#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
SMALL_RUN_TAG="${RUN_TAG:-small_real_lora_v3}"
DPO_RUN_TAG="${DPO_RUN_TAG:-${SMALL_RUN_TAG/small_real_lora/small_real_dpo}}"

echo "[loop] repo guard (preadd)"
"${PYTHON_BIN}" scripts/repo_guard.py --mode preadd --max-size-mb 10

echo "[loop] bootstrap minimal data assets"
"${PYTHON_BIN}" scripts/data/bootstrap_minimal_assets.py

echo "[loop] ensure real dataset"
bash scripts/data/ensure_real_dataset.sh || {
  echo "[loop] ensure-real-dataset failed; continue with minimal assets"
}

echo "[loop] small real pipeline"
RUN_TAG="${SMALL_RUN_TAG}" bash scripts/train/run_small_real_pipeline.sh || {
  echo "[loop] small-real failed; continue to build non-training artifacts"
}

echo "[loop] small real dpo pipeline"
RUN_TAG="${DPO_RUN_TAG}" bash scripts/train/run_small_real_dpo_pipeline.sh || {
  echo "[loop] small-real-dpo failed; continue to build non-training artifacts"
}

echo "[loop] dpo beta ablation"
bash scripts/train/run_small_real_dpo_ablation.sh || {
  echo "[loop] dpo-ablation failed; continue to build non-training artifacts"
}

echo "[loop] qwen layer-b (autofallback/blocker)"
bash scripts/train/run_layer_b_qwen_autofallback.sh || {
  echo "[loop] qwen layer-b failed (non-recoverable this round)"
}

echo "[loop] real alignment pipeline"
ALIGNMENT_MODE="${ALIGNMENT_MODE:-real}" \
SKIP_LAYER_B="${SKIP_LAYER_B:-1}" \
DPO_MAX_STEPS="${DPO_MAX_STEPS:-40}" \
DPO_EPOCHS="${DPO_EPOCHS:-1}" \
DPO_MAX_LENGTH="${DPO_MAX_LENGTH:-192}" \
bash scripts/train/run_real_alignment_pipeline.sh || {
  echo "[loop] real-alignment failed; continue to build non-training artifacts"
}

echo "[loop] baseline audit table"
"${PYTHON_BIN}" scripts/audit/build_baseline_audit_table.py --small-real-run-tag "${SMALL_RUN_TAG}"

echo "[loop] iteration report"
"${PYTHON_BIN}" scripts/audit/build_iteration_report.py --run-tag "${SMALL_RUN_TAG}"

echo "[loop] decision log"
"${PYTHON_BIN}" scripts/audit/update_decision_log.py

echo "[loop] thesis ready package"
"${PYTHON_BIN}" scripts/audit/build_thesis_ready_package.py

echo "[loop] done"
