#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
PREF_FILE="${PREF_FILE:-data/clean/real_pref_seed_pairs.jsonl}"
KB_FILE="${KB_FILE:-data/kg/real_medqa_reference_kb.jsonl}"
ALIGNMENT_MODE="${ALIGNMENT_MODE:-proxy}"  # proxy | real
ALLOW_PROXY_FALLBACK="${ALLOW_PROXY_FALLBACK:-0}"

run_proxy_alignment() {
  echo "[warn] run proxy alignment trainers."

  "${PYTHON_BIN}" src/train/dpo_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/dpo-real-baseline \
    --metrics-out reports/training/dpo_metrics.json

  "${PYTHON_BIN}" src/train/simpo_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/simpo-real-baseline \
    --metrics-out reports/training/simpo_metrics.json

  "${PYTHON_BIN}" src/train/kto_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/kto-real-baseline \
    --metrics-out reports/training/kto_metrics.json

  "${PYTHON_BIN}" src/train/compare_alignment.py \
    --dpo reports/training/dpo_metrics.json \
    --simpo reports/training/simpo_metrics.json \
    --kto reports/training/kto_metrics.json \
    --output reports/alignment_compare.md
}

# Step 1: real SFT (Layer-B baseline), skip automatically when no GPU.
if command -v nvidia-smi >/dev/null 2>&1 && [[ "${SKIP_LAYER_B:-0}" != "1" ]]; then
  TRAIN_FILE="${TRAIN_FILE}" \
  DEV_FILE="${DEV_FILE}" \
  OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/layer_b/qwen25_7b_sft}" \
  LOGGING_DIR="${LOGGING_DIR:-logs/layer_b/qwen25_7b_sft}" \
  METRICS_OUT="${METRICS_OUT:-reports/training/layer_b_qwen25_7b_sft_metrics.json}" \
  PYTHON_BIN="${PYTHON_BIN}" \
  bash scripts/train/run_layer_b_real_sft.sh
else
  echo "[warn] skip Layer-B SFT (no GPU or SKIP_LAYER_B=1), continue alignment stage."
  if [[ ! -f "${TRAIN_FILE}" ]]; then
    echo "[warn] train file missing: ${TRAIN_FILE}, fallback to small-real data."
    TRAIN_FILE="data/clean/sft_train.jsonl"
    DEV_FILE="data/clean/sft_dev.jsonl"
    "${PYTHON_BIN}" scripts/data/run_data_governance_pipeline.py --seed 42
  fi
  if [[ ! -f "${KB_FILE}" ]]; then
    echo "[warn] kb file missing: ${KB_FILE}, fallback to demo kg."
    KB_FILE="data/kg/cmekg_demo.jsonl"
  fi
fi

# Step 2: build preference pairs
"${PYTHON_BIN}" src/train/hard_negative_builder.py \
  --input "${TRAIN_FILE}" \
  --kg "${KB_FILE}" \
  --output "${PREF_FILE}"

if [[ "${ALIGNMENT_MODE}" == "proxy" ]]; then
  echo "[warn] ALIGNMENT_MODE=proxy"
  run_proxy_alignment
elif [[ "${ALIGNMENT_MODE}" == "real" ]]; then
  echo "[real] running real DPO + real SimPO/KTO with unified fallback."

  DPO_MODEL_PRIMARY="${DPO_MODEL_PRIMARY:-Qwen/Qwen2.5-0.5B-Instruct}"
  DPO_MODEL_FALLBACK="${DPO_MODEL_FALLBACK:-checkpoints/fallback_models/alignment_tiny_gpt2}"
  DPO_PRIMARY_TIMEOUT="${DPO_PRIMARY_TIMEOUT:-300}"
  SIMPO_PRIMARY_TIMEOUT="${SIMPO_PRIMARY_TIMEOUT:-240}"
  KTO_PRIMARY_TIMEOUT="${KTO_PRIMARY_TIMEOUT:-240}"
  DPO_FALLBACK_TIMEOUT="${DPO_FALLBACK_TIMEOUT:-0}"
  SIMPO_FALLBACK_TIMEOUT="${SIMPO_FALLBACK_TIMEOUT:-0}"
  KTO_FALLBACK_TIMEOUT="${KTO_FALLBACK_TIMEOUT:-0}"

  run_with_timeout() {
    local timeout_sec="$1"
    shift
    local cmd=("$@")
    local timeout_prefix=()
    if [[ "${timeout_sec}" -gt 0 ]]; then
      if command -v gtimeout >/dev/null 2>&1; then
        timeout_prefix=(gtimeout "${timeout_sec}")
      elif command -v timeout >/dev/null 2>&1; then
        timeout_prefix=(timeout "${timeout_sec}")
      fi
    fi

    if [[ ${#timeout_prefix[@]} -gt 0 ]]; then
      "${timeout_prefix[@]}" "${cmd[@]}"
    else
      "${cmd[@]}"
    fi
  }

  ensure_local_fallback_model() {
    if [[ ! -d "${DPO_MODEL_FALLBACK}" ]]; then
      echo "[real] prepare local fallback model: ${DPO_MODEL_FALLBACK}"
      "${PYTHON_BIN}" scripts/train/prepare_alignment_fallback_model.py --output-dir "${DPO_MODEL_FALLBACK}"
    fi
  }

  run_real_pref_trainer() {
    local name="$1"
    local script_path="$2"
    local proxy_script="$3"
    local task_name="$4"
    local out_dir="$5"
    local log_dir="$6"
    local metrics_path="$7"
    local primary_timeout="$8"
    local fallback_timeout="$9"
    shift 9
    local extra_args=("$@")

    local primary_cmd=(
      "${PYTHON_BIN}" "${script_path}"
      --task "${task_name}"
      --pref-file "${PREF_FILE}"
      --model-name "${DPO_MODEL_PRIMARY}"
      --output-dir "${out_dir}"
      --logging-dir "${log_dir}"
      --metrics-out "${metrics_path}"
      --epochs "${DPO_EPOCHS:-2}"
      --max-steps "${DPO_MAX_STEPS:-40}"
      --learning-rate "${DPO_LR:-1e-5}"
      --max-length "${DPO_MAX_LENGTH:-256}"
      --seed "${DPO_SEED:-42}"
      --trust-remote-code true
      --local-files-only false
      "${extra_args[@]}"
    )

    if run_with_timeout "${primary_timeout}" "${primary_cmd[@]}"; then
      echo "[real] ${name} primary model success."
      return 0
    fi
    echo "[real] ${name} primary model failed; fallback to local tiny real model."

    ensure_local_fallback_model

    local fallback_cmd=(
      "${PYTHON_BIN}" "${script_path}"
      --task "${task_name}_fallback"
      --pref-file "${PREF_FILE}"
      --model-name "${DPO_MODEL_FALLBACK}"
      --output-dir "${out_dir}"
      --logging-dir "${log_dir}"
      --metrics-out "${metrics_path}"
      --epochs "${DPO_EPOCHS:-2}"
      --max-steps "${DPO_MAX_STEPS:-40}"
      --learning-rate "${DPO_LR:-1e-5}"
      --max-length "${DPO_MAX_LENGTH:-256}"
      --seed "${DPO_SEED:-42}"
      --trust-remote-code false
      --local-files-only true
      "${extra_args[@]}"
    )

    if HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 run_with_timeout "${fallback_timeout}" "${fallback_cmd[@]}"; then
      echo "[real] ${name} local tiny real fallback success."
      return 0
    fi

    echo "[real] ${name} tiny real fallback failed."
    if [[ "${ALLOW_PROXY_FALLBACK}" == "1" ]]; then
      echo "[warn] ALLOW_PROXY_FALLBACK=1, downgrade ${name} to proxy trainer."
      "${PYTHON_BIN}" "${proxy_script}" \
        --pref-file "${PREF_FILE}" \
        --output-dir "${out_dir}" \
        --metrics-out "${metrics_path}" \
        --task "${task_name}_proxy_fallback"
      return 0
    fi

    echo "[error] ${name} failed in real mode and proxy fallback disabled."
    return 1
  }

  run_real_pref_trainer \
    "DPO" \
    "src/train/real_dpo_train.py" \
    "src/train/dpo_train.py" \
    "real_dpo_alignment" \
    "checkpoints/dpo-real-baseline" \
    "logs/dpo-real-baseline" \
    "reports/training/dpo_real_metrics.json" \
    "${DPO_PRIMARY_TIMEOUT}" \
    "${DPO_FALLBACK_TIMEOUT}"

  run_real_pref_trainer \
    "SimPO" \
    "src/train/real_simpo_train.py" \
    "src/train/simpo_train.py" \
    "real_simpo_alignment" \
    "checkpoints/simpo-real-baseline" \
    "logs/simpo-real-baseline" \
    "reports/training/simpo_metrics.json" \
    "${SIMPO_PRIMARY_TIMEOUT}" \
    "${SIMPO_FALLBACK_TIMEOUT}" \
    --beta "${SIMPO_BETA:-1.0}" \
    --gamma "${SIMPO_GAMMA:-0.03}"

  run_real_pref_trainer \
    "KTO" \
    "src/train/real_kto_train.py" \
    "src/train/kto_train.py" \
    "real_kto_alignment" \
    "checkpoints/kto-real-baseline" \
    "logs/kto-real-baseline" \
    "reports/training/kto_metrics.json" \
    "${KTO_PRIMARY_TIMEOUT}" \
    "${KTO_FALLBACK_TIMEOUT}" \
    --loss-aversion "${KTO_LOSS_AVERSION:-1.5}" \
    --tau "${KTO_TAU:-1.0}"

  if [[ -f "reports/training/dpo_real_metrics.json" ]]; then
    dpo_compare_input="reports/training/dpo_real_metrics.json"
  else
    dpo_compare_input="reports/training/dpo_metrics.json"
  fi

  "${PYTHON_BIN}" src/train/compare_alignment.py \
    --dpo "${dpo_compare_input}" \
    --simpo reports/training/simpo_metrics.json \
    --kto reports/training/kto_metrics.json \
    --output reports/alignment_compare.md
else
  echo "[error] ALIGNMENT_MODE must be one of: proxy, real"
  exit 1
fi

echo "[real-alignment-pipeline] done mode=${ALIGNMENT_MODE}"
