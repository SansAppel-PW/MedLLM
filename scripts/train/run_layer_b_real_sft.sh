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

python3 src/train/real_sft_train.py \
  --config "${CONFIG}" \
  --task real_sft_layer_b \
  --model-name "${MODEL_NAME}" \
  --train-file "${TRAIN_FILE}" \
  --dev-file "${DEV_FILE}" \
  --output-dir "${OUTPUT_DIR}" \
  --logging-dir "${LOGGING_DIR}" \
  --metrics-out "${METRICS_OUT}" \
  --max-length "${MAX_LENGTH:-2048}" \
  --num-train-epochs "${NUM_EPOCHS:-1}" \
  --max-steps "${MAX_STEPS:--1}" \
  --learning-rate "${LR:-2e-5}" \
  --weight-decay "${WEIGHT_DECAY:-0.01}" \
  --warmup-ratio "${WARMUP_RATIO:-0.03}" \
  --per-device-train-batch-size "${TRAIN_BSZ:-1}" \
  --per-device-eval-batch-size "${EVAL_BSZ:-1}" \
  --gradient-accumulation-steps "${GRAD_ACC:-16}" \
  --gradient-checkpointing "${GRAD_CKPT:-true}" \
  --logging-steps "${LOG_STEPS:-10}" \
  --save-steps "${SAVE_STEPS:-100}" \
  --eval-steps "${EVAL_STEPS:-100}" \
  --seed "${SEED:-42}" \
  --use-lora "${USE_LORA:-true}" \
  --lora-r "${LORA_R:-64}" \
  --lora-alpha "${LORA_ALPHA:-128}" \
  --lora-dropout "${LORA_DROPOUT:-0.05}" \
  --lora-target-modules "${LORA_TARGETS:-q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj}" \
  --load-in-4bit "${LOAD_IN_4BIT:-true}" \
  --bf16 "${BF16:-true}" \
  --fp16 "${FP16:-false}"

echo "[layer-b-real-sft] done"
