#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
RUN_TAG="${RUN_TAG:-small_real_dpo_v1}"
SEED="${SEED:-42}"

PREF_FILE="${PREF_FILE:-data/clean/pref_seed_pairs.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/alignment/${RUN_TAG}}"
LOGGING_DIR="${LOGGING_DIR:-logs/alignment/${RUN_TAG}}"
METRICS_OUT="${METRICS_OUT:-reports/training/${RUN_TAG}_metrics.json}"

MODEL_PRIMARY="${MODEL_PRIMARY:-Qwen/Qwen2.5-0.5B-Instruct}"
MODEL_FALLBACK="${MODEL_FALLBACK:-${HOME}/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be}"
PRIMARY_TIMEOUT="${PRIMARY_TIMEOUT:-300}"

mkdir -p "$(dirname "${METRICS_OUT}")" "${LOGGING_DIR}"

echo "[small-real-dpo] step1 prepare_data"
"${PYTHON_BIN}" scripts/data/run_data_governance_pipeline.py --seed "${SEED}"

run_dpo() {
  local model_name="$1"
  local local_files_only="$2"
  local offline="$3"
  local timeout_sec="${4:-0}"
  local -a extra_env=()
  if [[ "${offline}" == "1" ]]; then
    extra_env+=(HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1)
  fi
  local -a cmd=(
    "${PYTHON_BIN}" src/train/real_dpo_train.py
    --task "${RUN_TAG}"
    --pref-file "${PREF_FILE}"
    --model-name "${model_name}"
    --output-dir "${OUTPUT_DIR}"
    --logging-dir "${LOGGING_DIR}"
    --metrics-out "${METRICS_OUT}"
    --epochs "${EPOCHS:-2}"
    --max-steps "${MAX_STEPS:-16}"
    --learning-rate "${LR:-1e-5}"
    --weight-decay "${WEIGHT_DECAY:-0.0}"
    --beta "${BETA:-0.1}"
    --max-length "${MAX_LENGTH:-256}"
    --seed "${SEED}"
    --trust-remote-code true
    --local-files-only "${local_files_only}"
  )
  local -a final_cmd=()
  if [[ "${#extra_env[@]}" -gt 0 ]]; then
    final_cmd=(env "${extra_env[@]}" "${cmd[@]}")
  else
    final_cmd=("${cmd[@]}")
  fi

  if [[ "${timeout_sec}" -gt 0 ]]; then
    (
      "${final_cmd[@]}" &
      local cmd_pid=$!
      (
        sleep "${timeout_sec}"
        if kill -0 "${cmd_pid}" 2>/dev/null; then
          echo "[small-real-dpo] timeout ${timeout_sec}s reached, terminate pid=${cmd_pid}"
          kill "${cmd_pid}" 2>/dev/null || true
        fi
      ) &
      local watchdog_pid=$!
      wait "${cmd_pid}"
      local rc=$?
      kill "${watchdog_pid}" 2>/dev/null || true
      wait "${watchdog_pid}" 2>/dev/null || true
      exit "${rc}"
    )
  else
    "${final_cmd[@]}"
  fi
}

echo "[small-real-dpo] step2 train"
if ! run_dpo "${MODEL_PRIMARY}" false 0 "${PRIMARY_TIMEOUT}"; then
  echo "[small-real-dpo] primary model failed, trying fallback: ${MODEL_FALLBACK}"
  if [[ ! -d "${MODEL_FALLBACK}" ]]; then
    echo "[small-real-dpo] fallback model path not found: ${MODEL_FALLBACK}" >&2
    exit 1
  fi
  run_dpo "${MODEL_FALLBACK}" true 1 0
fi

echo "[small-real-dpo] done run_tag=${RUN_TAG}"
