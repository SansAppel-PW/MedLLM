#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
PREF_FILE="${PREF_FILE:-data/clean/real_pref_seed_pairs.jsonl}"
KB_FILE="${KB_FILE:-data/kg/real_medqa_reference_kb.jsonl}"
ALIGNMENT_MODE="${ALIGNMENT_MODE:-proxy}"  # proxy | real
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"

SFT_OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/layer_b/qwen25_7b_sft}"
SFT_LOGGING_DIR="${LOGGING_DIR:-logs/layer_b/qwen25_7b_sft}"
SFT_METRICS_OUT="${METRICS_OUT:-reports/training/layer_b_qwen25_7b_sft_metrics.json}"

ALIGN_MAX_STEPS="${ALIGN_MAX_STEPS:-200}"
ALIGN_MAX_PAIRS="${ALIGN_MAX_PAIRS:-0}"
ALIGN_MAX_LENGTH="${ALIGN_MAX_LENGTH:-1024}"
ALIGN_LR="${ALIGN_LR:-1e-6}"
ALIGN_TRAIN_BSZ="${ALIGN_TRAIN_BSZ:-1}"
ALIGN_GRAD_ACC="${ALIGN_GRAD_ACC:-16}"
ALIGN_LOG_STEPS="${ALIGN_LOG_STEPS:-10}"
ALIGN_SAVE_STEPS="${ALIGN_SAVE_STEPS:-100}"
ALIGN_SAVE_TOTAL_LIMIT="${ALIGN_SAVE_TOTAL_LIMIT:-2}"
ALIGN_LOAD_IN_4BIT="${ALIGN_LOAD_IN_4BIT:-true}"
ALIGN_BF16="${ALIGN_BF16:-true}"
ALIGN_FP16="${ALIGN_FP16:-false}"
ALIGN_USE_LORA="${ALIGN_USE_LORA:-true}"
ALIGN_LORA_R="${ALIGN_LORA_R:-32}"
ALIGN_LORA_ALPHA="${ALIGN_LORA_ALPHA:-64}"
ALIGN_LORA_DROPOUT="${ALIGN_LORA_DROPOUT:-0.05}"
ALIGN_LORA_TARGETS="${ALIGN_LORA_TARGETS:-q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj}"

run_real_pref_with_retry() {
  local method="$1"
  local config="$2"
  local out_dir="$3"
  local log_dir="$4"
  local metrics_out="$5"

  local bsz="${ALIGN_TRAIN_BSZ}"
  local grad_acc="${ALIGN_GRAD_ACC}"
  local save_total_limit="${ALIGN_SAVE_TOTAL_LIMIT}"
  local attempt=1
  while (( attempt <= 3 )); do
    mkdir -p "${log_dir}"
    local attempt_log="${log_dir}/attempt_${attempt}.log"
    echo "[real-${method}] attempt=${attempt} bsz=${bsz} grad_acc=${grad_acc}"
    set +e
    python3 src/train/real_pref_train.py \
      --config "${config}" \
      --task "real_${method}" \
      --method "${method}" \
      --model-name "${MODEL_NAME}" \
      --pref-file "${PREF_FILE}" \
      --output-dir "${out_dir}" \
      --logging-dir "${log_dir}" \
      --metrics-out "${metrics_out}" \
      --max-length "${ALIGN_MAX_LENGTH}" \
      --max-pairs "${ALIGN_MAX_PAIRS}" \
      --num-train-epochs "${ALIGN_NUM_EPOCHS:-1}" \
      --max-steps "${ALIGN_MAX_STEPS}" \
      --learning-rate "${ALIGN_LR}" \
      --weight-decay "${ALIGN_WEIGHT_DECAY:-0.01}" \
      --warmup-ratio "${ALIGN_WARMUP_RATIO:-0.03}" \
      --per-device-train-batch-size "${bsz}" \
      --gradient-accumulation-steps "${grad_acc}" \
      --gradient-checkpointing "${ALIGN_GRAD_CKPT:-true}" \
      --logging-steps "${ALIGN_LOG_STEPS}" \
      --save-steps "${ALIGN_SAVE_STEPS}" \
      --save-total-limit "${save_total_limit}" \
      --seed "${ALIGN_SEED:-42}" \
      --beta "${ALIGN_BETA:-0.1}" \
      --target-margin "${ALIGN_TARGET_MARGIN:-0.5}" \
      --use-lora "${ALIGN_USE_LORA}" \
      --lora-r "${ALIGN_LORA_R}" \
      --lora-alpha "${ALIGN_LORA_ALPHA}" \
      --lora-dropout "${ALIGN_LORA_DROPOUT}" \
      --lora-target-modules "${ALIGN_LORA_TARGETS}" \
      --load-in-4bit "${ALIGN_LOAD_IN_4BIT}" \
      --bf16 "${ALIGN_BF16}" \
      --fp16 "${ALIGN_FP16}" >"${attempt_log}" 2>&1
    local rc=$?
    set -e
    cat "${attempt_log}"
    if [[ ${rc} -eq 0 ]]; then
      return 0
    fi
    if grep -Eqi "out of memory|cuda oom" "${attempt_log}"; then
      echo "[real-${method}] OOM detected, auto-adjust and retry."
      bsz=1
      grad_acc=$((grad_acc * 2))
      save_total_limit=2
      attempt=$((attempt + 1))
      continue
    fi
    return "${rc}"
  done
  echo "[real-${method}] failed after 3 attempts"
  return 1
}

# Step 1: real SFT (Layer-B baseline)
TRAIN_FILE="${TRAIN_FILE}" \
DEV_FILE="${DEV_FILE}" \
MODEL_NAME="${MODEL_NAME}" \
OUTPUT_DIR="${SFT_OUTPUT_DIR}" \
LOGGING_DIR="${SFT_LOGGING_DIR}" \
METRICS_OUT="${SFT_METRICS_OUT}" \
bash scripts/train/run_layer_b_real_sft.sh

# Step 2: build preference pairs
python3 src/train/hard_negative_builder.py \
  --input "${TRAIN_FILE}" \
  --kg "${KB_FILE}" \
  --output "${PREF_FILE}"

if [[ "${ALIGNMENT_MODE}" == "proxy" ]]; then
  echo "[warn] ALIGNMENT_MODE=proxy: DPO/SimPO/KTO will run simulated trainers."

  python3 src/train/dpo_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/dpo-real-baseline \
    --metrics-out reports/training/dpo_metrics.json

  python3 src/train/simpo_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/simpo-real-baseline \
    --metrics-out reports/training/simpo_metrics.json

  python3 src/train/kto_train.py \
    --pref-file "${PREF_FILE}" \
    --output-dir checkpoints/kto-real-baseline \
    --metrics-out reports/training/kto_metrics.json
elif [[ "${ALIGNMENT_MODE}" == "real" ]]; then
  run_real_pref_with_retry \
    dpo \
    configs/train/dpo_real.yaml \
    checkpoints/dpo-real-baseline \
    logs/dpo-real-baseline \
    reports/training/dpo_metrics.json

  run_real_pref_with_retry \
    simpo \
    configs/train/simpo_real.yaml \
    checkpoints/simpo-real-baseline \
    logs/simpo-real-baseline \
    reports/training/simpo_metrics.json

  run_real_pref_with_retry \
    kto \
    configs/train/kto_real.yaml \
    checkpoints/kto-real-baseline \
    logs/kto-real-baseline \
    reports/training/kto_metrics.json
else
  echo "[error] ALIGNMENT_MODE must be one of: proxy, real"
  exit 1
fi

python3 src/train/compare_alignment.py \
  --dpo reports/training/dpo_metrics.json \
  --simpo reports/training/simpo_metrics.json \
  --kto reports/training/kto_metrics.json \
  --output reports/alignment_compare.md

echo "[real-alignment-pipeline] done mode=${ALIGNMENT_MODE}"
