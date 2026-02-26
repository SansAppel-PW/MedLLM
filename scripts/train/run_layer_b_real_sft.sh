#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

CONFIG="${CONFIG:-configs/train/sft_layer_b_real.yaml}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"
OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/layer_b/qwen25_7b_sft}"
LOGGING_DIR="${LOGGING_DIR:-logs/layer_b/qwen25_7b_sft}"
METRICS_OUT="${METRICS_OUT:-reports/training/layer_b_qwen25_7b_sft_metrics.json}"

MAX_LENGTH="${MAX_LENGTH:-2048}"
NUM_EPOCHS="${NUM_EPOCHS:-1}"
MAX_STEPS="${MAX_STEPS:--1}"
LR="${LR:-2e-5}"
WEIGHT_DECAY="${WEIGHT_DECAY:-0.01}"
WARMUP_RATIO="${WARMUP_RATIO:-0.03}"
OPTIM="${OPTIM:-paged_adamw_8bit}"
TRAIN_BSZ="${TRAIN_BSZ:-1}"
EVAL_BSZ="${EVAL_BSZ:-1}"
GRAD_ACC="${GRAD_ACC:-16}"
GRAD_CKPT="${GRAD_CKPT:-true}"
NUM_WORKERS="${NUM_WORKERS:-2}"
LOG_STEPS="${LOG_STEPS:-10}"
SAVE_STEPS="${SAVE_STEPS:-100}"
EVAL_STEPS="${EVAL_STEPS:-100}"
SAVE_TOTAL_LIMIT="${SAVE_TOTAL_LIMIT:-2}"
SEED="${SEED:-42}"
USE_LORA="${USE_LORA:-true}"
LORA_R="${LORA_R:-64}"
LORA_ALPHA="${LORA_ALPHA:-128}"
LORA_DROPOUT="${LORA_DROPOUT:-0.05}"
LORA_TARGETS="${LORA_TARGETS:-q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj}"
LOAD_IN_4BIT="${LOAD_IN_4BIT:-true}"
BF16="${BF16:-true}"
FP16="${FP16:-false}"

run_once() {
  python3 src/train/real_sft_train.py \
    --config "${CONFIG}" \
    --task real_sft_layer_b \
    --model-name "${MODEL_NAME}" \
    --train-file "${TRAIN_FILE}" \
    --dev-file "${DEV_FILE}" \
    --output-dir "${OUTPUT_DIR}" \
    --logging-dir "${LOGGING_DIR}" \
    --metrics-out "${METRICS_OUT}" \
    --max-length "${MAX_LENGTH}" \
    --num-train-epochs "${NUM_EPOCHS}" \
    --max-steps "${MAX_STEPS}" \
    --learning-rate "${LR}" \
    --weight-decay "${WEIGHT_DECAY}" \
    --warmup-ratio "${WARMUP_RATIO}" \
    --optim "${OPTIM}" \
    --per-device-train-batch-size "${TRAIN_BSZ}" \
    --per-device-eval-batch-size "${EVAL_BSZ}" \
    --gradient-accumulation-steps "${GRAD_ACC}" \
    --gradient-checkpointing "${GRAD_CKPT}" \
    --num-workers "${NUM_WORKERS}" \
    --logging-steps "${LOG_STEPS}" \
    --save-steps "${SAVE_STEPS}" \
    --eval-steps "${EVAL_STEPS}" \
    --save-total-limit "${SAVE_TOTAL_LIMIT}" \
    --seed "${SEED}" \
    --use-lora "${USE_LORA}" \
    --lora-r "${LORA_R}" \
    --lora-alpha "${LORA_ALPHA}" \
    --lora-dropout "${LORA_DROPOUT}" \
    --lora-target-modules "${LORA_TARGETS}" \
    --load-in-4bit "${LOAD_IN_4BIT}" \
    --bf16 "${BF16}" \
    --fp16 "${FP16}"
}

attempt=1
while (( attempt <= 3 )); do
  mkdir -p "${LOGGING_DIR}"
  attempt_log="${LOGGING_DIR}/train_attempt_${attempt}.log"
  echo "[layer-b-real-sft] attempt=${attempt} bsz=${TRAIN_BSZ} grad_acc=${GRAD_ACC}"
  set +e
  run_once >"${attempt_log}" 2>&1
  rc=$?
  set -e
  cat "${attempt_log}"
  if [[ ${rc} -eq 0 ]]; then
    echo "[layer-b-real-sft] done"
    exit 0
  fi
  if grep -Eqi "out of memory|cuda oom" "${attempt_log}"; then
    echo "[layer-b-real-sft] OOM detected, auto-adjust and retry."
    TRAIN_BSZ=1
    GRAD_ACC=$((GRAD_ACC * 2))
    GRAD_CKPT=true
    SAVE_TOTAL_LIMIT=2
    attempt=$((attempt + 1))
    continue
  fi
  exit ${rc}
done

echo "[layer-b-real-sft] failed after 3 attempts"
exit 1
