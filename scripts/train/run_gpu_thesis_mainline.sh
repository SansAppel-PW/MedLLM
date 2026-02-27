#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
DRY_RUN="${DRY_RUN:-0}"
REQUIRE_GPU="${REQUIRE_GPU:-1}"

ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-0}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-200}"

run_cmd() {
  echo "[gpu-mainline] $*"
  if [[ "${DRY_RUN}" == "1" ]]; then
    return 0
  fi
  "$@"
}

if [[ "${REQUIRE_GPU}" == "1" && "${DRY_RUN}" != "1" ]]; then
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "[gpu-mainline] ERROR: nvidia-smi not found. Please run this script on a CUDA GPU host." >&2
    exit 2
  fi
fi

run_cmd "${PYTHON_BIN}" scripts/repo_guard.py --mode preadd --max-size-mb 10
run_cmd "${PYTHON_BIN}" scripts/data/bootstrap_minimal_assets.py
run_cmd bash scripts/data/ensure_real_dataset.sh

run_cmd bash scripts/train/run_layer_b_qwen_autofallback.sh

run_cmd env \
  ALIGNMENT_MODE=real \
  SKIP_LAYER_B=1 \
  DPO_EPOCHS="${DPO_EPOCHS:-1}" \
  DPO_MAX_STEPS="${DPO_MAX_STEPS:-120}" \
  DPO_MAX_LENGTH="${DPO_MAX_LENGTH:-512}" \
  SIMPO_PRIMARY_TIMEOUT="${SIMPO_PRIMARY_TIMEOUT:-0}" \
  KTO_PRIMARY_TIMEOUT="${KTO_PRIMARY_TIMEOUT:-0}" \
  bash scripts/train/run_real_alignment_pipeline.sh

run_cmd env \
  ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
  JUDGE_MODEL="${JUDGE_MODEL}" \
  JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES}" \
  KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}" \
  EVAL_SPLITS="${EVAL_SPLITS:-validation,test}" \
  DET_MAX="${DET_MAX:-0}" \
  EVAL_MAX="${EVAL_MAX:-0}" \
  SOTA_MAX="${SOTA_MAX:-0}" \
  LOG_EVERY="${LOG_EVERY:-300}" \
  bash scripts/eval/run_thesis_pipeline.sh

run_cmd "${PYTHON_BIN}" scripts/audit/build_thesis_ready_package.py
run_cmd "${PYTHON_BIN}" scripts/audit/build_iteration_report.py
run_cmd "${PYTHON_BIN}" scripts/audit/update_decision_log.py
run_cmd "${PYTHON_BIN}" scripts/audit/check_opening_alignment.py
run_cmd "${PYTHON_BIN}" scripts/audit/check_task_completion.py
run_cmd "${PYTHON_BIN}" scripts/audit/verify_gpu_experiment_closure.py --strict

echo "[gpu-mainline] done"

