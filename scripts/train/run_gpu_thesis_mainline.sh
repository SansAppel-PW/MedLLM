#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
DRY_RUN="${DRY_RUN:-0}"
REQUIRE_GPU="${REQUIRE_GPU:-1}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
LAYER_B_OPTIONAL="${LAYER_B_OPTIONAL:-1}"
THESIS_EVAL_AUTOFALLBACK="${THESIS_EVAL_AUTOFALLBACK:-1}"

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

run_cmd_may_fail() {
  echo "[gpu-mainline] $*"
  if [[ "${DRY_RUN}" == "1" ]]; then
    return 0
  fi
  set +e
  "$@"
  local rc=$?
  set -e
  return "${rc}"
}

setup_hf_cache_defaults() {
  if [[ -z "${HF_HOME:-}" && -d "/root/autodl-tmp" && -w "/root/autodl-tmp" ]]; then
    export HF_HOME="/root/autodl-tmp/hf-cache"
  fi
  if [[ -n "${HF_HOME:-}" ]]; then
    export HF_HUB_CACHE="${HF_HUB_CACHE:-${HF_HOME}/hub}"
    export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-${HF_HOME}/transformers}"
    mkdir -p "${HF_HOME}" "${HF_HUB_CACHE}" "${TRANSFORMERS_CACHE}"
    echo "[gpu-mainline] HF_HOME=${HF_HOME}"
    echo "[gpu-mainline] HF_HUB_CACHE=${HF_HUB_CACHE}"
    echo "[gpu-mainline] TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}"
  fi
}

run_layer_b_with_policy() {
  local rc=0
  run_cmd_may_fail env \
    USE_TORCHRUN="${USE_TORCHRUN:-0}" \
    NUM_GPUS="${NUM_GPUS:-1}" \
    BF16="${BF16:-}" \
    FP16="${FP16:-}" \
    bash scripts/train/run_layer_b_qwen_autofallback.sh
  rc=$?
  if [[ ${rc} -eq 0 ]]; then
    return 0
  fi
  if [[ "${LAYER_B_OPTIONAL}" == "1" ]]; then
    echo "[gpu-mainline] warning: Layer-B failed (rc=${rc}), continue with alignment/eval."
    return 0
  fi
  echo "[gpu-mainline] error: Layer-B failed and LAYER_B_OPTIONAL=0."
  return "${rc}"
}

run_thesis_pipeline_with_fallback() {
  local det_base="${DET_MAX:-0}"
  local eval_base="${EVAL_MAX:-0}"
  local sota_base="${SOTA_MAX:-0}"
  local det_list=("${det_base}" "800" "200")
  local eval_list=("${eval_base}" "1200" "400")
  local sota_list=("${sota_base}" "800" "300")
  local rc=0
  local attempt=1
  local max_attempts=1
  if [[ "${THESIS_EVAL_AUTOFALLBACK}" == "1" ]]; then
    max_attempts=3
  fi

  while (( attempt <= max_attempts )); do
    local idx=$((attempt - 1))
    local det="${det_list[$idx]}"
    local evl="${eval_list[$idx]}"
    local sot="${sota_list[$idx]}"
    echo "[gpu-mainline] thesis-pipeline attempt=${attempt} DET_MAX=${det} EVAL_MAX=${evl} SOTA_MAX=${sot}"
    if run_cmd_may_fail env \
      PYTHON_BIN="${PYTHON_BIN}" \
      ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
      JUDGE_MODEL="${JUDGE_MODEL}" \
      JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES}" \
      KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}" \
      EVAL_SPLITS="${EVAL_SPLITS:-validation,test}" \
      DET_MAX="${det}" \
      EVAL_MAX="${evl}" \
      SOTA_MAX="${sot}" \
      LOG_EVERY="${LOG_EVERY:-300}" \
      bash scripts/eval/run_thesis_pipeline.sh; then
      return 0
    fi
    rc=$?
    echo "[gpu-mainline] warning: thesis-pipeline attempt=${attempt} failed rc=${rc}"
    attempt=$((attempt + 1))
  done
  return "${rc}"
}

if [[ "${REQUIRE_GPU}" == "1" && "${DRY_RUN}" != "1" ]]; then
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "[gpu-mainline] ERROR: nvidia-smi not found. Please run this script on a CUDA GPU host." >&2
    exit 2
  fi
fi

setup_hf_cache_defaults
run_cmd "${PYTHON_BIN}" scripts/repo_guard.py --mode preadd --max-size-mb 10
run_cmd "${PYTHON_BIN}" scripts/audit/check_pipeline_interface_consistency.py
run_cmd "${PYTHON_BIN}" scripts/data/bootstrap_minimal_assets.py
run_cmd bash scripts/data/ensure_real_dataset.sh
echo "[gpu-mainline] HF_ENDPOINT=${HF_ENDPOINT}"

run_layer_b_with_policy

run_cmd env \
  PYTHON_BIN="${PYTHON_BIN}" \
  ALIGNMENT_MODE=real \
  SKIP_LAYER_B=1 \
  DPO_EPOCHS="${DPO_EPOCHS:-1}" \
  DPO_MAX_STEPS="${DPO_MAX_STEPS:-120}" \
  DPO_MAX_LENGTH="${DPO_MAX_LENGTH:-512}" \
  SIMPO_PRIMARY_TIMEOUT="${SIMPO_PRIMARY_TIMEOUT:-0}" \
  KTO_PRIMARY_TIMEOUT="${KTO_PRIMARY_TIMEOUT:-0}" \
  bash scripts/train/run_real_alignment_pipeline.sh

run_thesis_pipeline_with_fallback

run_cmd "${PYTHON_BIN}" scripts/audit/build_thesis_ready_package.py
run_cmd "${PYTHON_BIN}" scripts/audit/build_iteration_report.py
run_cmd "${PYTHON_BIN}" scripts/audit/update_decision_log.py
run_cmd "${PYTHON_BIN}" scripts/audit/check_opening_alignment.py
run_cmd "${PYTHON_BIN}" scripts/audit/check_task_completion.py
run_cmd "${PYTHON_BIN}" scripts/audit/verify_gpu_experiment_closure.py --strict

echo "[gpu-mainline] done"
