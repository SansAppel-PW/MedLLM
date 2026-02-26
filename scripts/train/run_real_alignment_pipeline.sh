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

# Step 1: real SFT (Layer-B baseline), skip automatically when no GPU.
if command -v nvidia-smi >/dev/null 2>&1 && [[ "${SKIP_LAYER_B:-0}" != "1" ]]; then
  TRAIN_FILE="${TRAIN_FILE}" \
  DEV_FILE="${DEV_FILE}" \
  OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/layer_b/qwen25_7b_sft}" \
  LOGGING_DIR="${LOGGING_DIR:-logs/layer_b/qwen25_7b_sft}" \
  METRICS_OUT="${METRICS_OUT:-reports/training/layer_b_qwen25_7b_sft_metrics.json}" \
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
  echo "[warn] ALIGNMENT_MODE=proxy: DPO/SimPO/KTO will run simulated trainers."

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
elif [[ "${ALIGNMENT_MODE}" == "real" ]]; then
  echo "[real] running real DPO + proxy SimPO/KTO hybrid alignment."

  DPO_MODEL_PRIMARY="${DPO_MODEL_PRIMARY:-Qwen/Qwen2.5-0.5B-Instruct}"
  DPO_MODEL_FALLBACK="${DPO_MODEL_FALLBACK:-${HOME}/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be}"
  DPO_PRIMARY_TIMEOUT="${DPO_PRIMARY_TIMEOUT:-300}"

  dpo_primary_cmd=(
    "${PYTHON_BIN}" src/train/real_dpo_train.py
    --task real_dpo_alignment \
    --pref-file "${PREF_FILE}" \
    --model-name "${DPO_MODEL_PRIMARY}" \
    --output-dir checkpoints/dpo-real-baseline \
    --logging-dir logs/dpo-real-baseline \
    --metrics-out reports/training/dpo_real_metrics.json \
    --epochs "${DPO_EPOCHS:-2}" \
    --max-steps "${DPO_MAX_STEPS:-40}" \
    --learning-rate "${DPO_LR:-1e-5}" \
    --max-length "${DPO_MAX_LENGTH:-256}" \
    --seed "${DPO_SEED:-42}" \
    --trust-remote-code true \
    --local-files-only false
  )

  timeout_prefix=()
  if [[ "${DPO_PRIMARY_TIMEOUT}" -gt 0 ]]; then
    if command -v gtimeout >/dev/null 2>&1; then
      timeout_prefix=(gtimeout "${DPO_PRIMARY_TIMEOUT}")
    elif command -v timeout >/dev/null 2>&1; then
      timeout_prefix=(timeout "${DPO_PRIMARY_TIMEOUT}")
    fi
  fi

  run_primary_ok=0
  if [[ ${#timeout_prefix[@]} -gt 0 ]]; then
    if "${timeout_prefix[@]}" "${dpo_primary_cmd[@]}"; then
      run_primary_ok=1
    else
      echo "[real] primary DPO run failed or timed out (${DPO_PRIMARY_TIMEOUT}s)."
    fi
  else
    if "${dpo_primary_cmd[@]}"; then
      run_primary_ok=1
    else
      echo "[real] primary DPO run failed."
    fi
  fi

  if [[ "${run_primary_ok}" -ne 1 ]]; then
    echo "[real] primary DPO model failed, fallback to local tiny model."
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "${PYTHON_BIN}" src/train/real_dpo_train.py \
      --task real_dpo_alignment_fallback \
      --pref-file "${PREF_FILE}" \
      --model-name "${DPO_MODEL_FALLBACK}" \
      --output-dir checkpoints/dpo-real-baseline \
      --logging-dir logs/dpo-real-baseline \
      --metrics-out reports/training/dpo_real_metrics.json \
      --epochs "${DPO_EPOCHS:-2}" \
      --max-steps "${DPO_MAX_STEPS:-40}" \
      --learning-rate "${DPO_LR:-1e-5}" \
      --max-length "${DPO_MAX_LENGTH:-256}" \
      --seed "${DPO_SEED:-42}" \
      --trust-remote-code false \
      --local-files-only true
  fi

  echo "[real] SimPO/KTO remain proxy in current stage."
  "${PYTHON_BIN}" src/train/simpo_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/simpo-real-baseline \
    --metrics-out reports/training/simpo_metrics.json

  "${PYTHON_BIN}" src/train/kto_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/kto-real-baseline \
    --metrics-out reports/training/kto_metrics.json

  "${PYTHON_BIN}" src/train/compare_alignment.py \
    --dpo reports/training/dpo_real_metrics.json \
    --simpo reports/training/simpo_metrics.json \
    --kto reports/training/kto_metrics.json \
    --output reports/alignment_compare.md
else
  echo "[error] ALIGNMENT_MODE must be one of: proxy, real"
  exit 1
fi

echo "[real-alignment-pipeline] done mode=${ALIGNMENT_MODE}"
