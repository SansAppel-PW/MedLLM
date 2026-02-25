#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
PREF_FILE="${PREF_FILE:-data/clean/real_pref_seed_pairs.jsonl}"
KB_FILE="${KB_FILE:-data/kg/real_medqa_reference_kb.jsonl}"

python3 src/train/sft_train.py \
  --train-file "${TRAIN_FILE}" \
  --dev-file "${DEV_FILE}" \
  --output-dir checkpoints/sft-real-baseline \
  --report reports/sft_baseline.md

python3 src/train/hard_negative_builder.py \
  --input "${TRAIN_FILE}" \
  --kg "${KB_FILE}" \
  --output "${PREF_FILE}"

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

echo "[real-alignment] done"
