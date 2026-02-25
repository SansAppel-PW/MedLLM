#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
PREF_FILE="${PREF_FILE:-data/clean/real_pref_seed_pairs.jsonl}"
KB_FILE="${KB_FILE:-data/kg/real_medqa_reference_kb.jsonl}"
ALIGNMENT_MODE="${ALIGNMENT_MODE:-proxy}"  # proxy | real

# Step 1: real SFT (Layer-B baseline)
TRAIN_FILE="${TRAIN_FILE}" \
DEV_FILE="${DEV_FILE}" \
OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/layer_b/qwen25_7b_sft}" \
LOGGING_DIR="${LOGGING_DIR:-logs/layer_b/qwen25_7b_sft}" \
METRICS_OUT="${METRICS_OUT:-reports/training/layer_b_qwen25_7b_sft_metrics.json}" \
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

  python3 src/train/compare_alignment.py \
    --dpo reports/training/dpo_metrics.json \
    --simpo reports/training/simpo_metrics.json \
    --kto reports/training/kto_metrics.json \
    --output reports/alignment_compare.md
elif [[ "${ALIGNMENT_MODE}" == "real" ]]; then
  echo "[todo] ALIGNMENT_MODE=real requires real DPO/SimPO/KTO trainers. Not implemented yet."
  exit 2
else
  echo "[error] ALIGNMENT_MODE must be one of: proxy, real"
  exit 1
fi

echo "[real-alignment-pipeline] done mode=${ALIGNMENT_MODE}"
