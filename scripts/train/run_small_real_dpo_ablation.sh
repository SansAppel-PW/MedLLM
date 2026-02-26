#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
SEED="${SEED:-42}"
MAX_STEPS="${MAX_STEPS:-8}"
EPOCHS="${EPOCHS:-2}"
MAX_LENGTH="${MAX_LENGTH:-256}"
BETAS="${BETAS:-0.05,0.10,0.20}"

MODEL_NAME="${MODEL_NAME:-${HOME}/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be}"
PREF_FILE="${PREF_FILE:-data/clean/pref_seed_pairs.jsonl}"

echo "[dpo-ablation] step1 prepare_data"
"${PYTHON_BIN}" scripts/data/run_data_governance_pipeline.py --seed "${SEED}"

if [[ ! -f "${PREF_FILE}" ]]; then
  echo "[dpo-ablation] pref file missing: ${PREF_FILE}" >&2
  exit 1
fi
if [[ ! -d "${MODEL_NAME}" ]]; then
  echo "[dpo-ablation] model path missing: ${MODEL_NAME}" >&2
  exit 1
fi

IFS=',' read -r -a beta_values <<< "${BETAS}"
for beta in "${beta_values[@]}"; do
  beta_trimmed="$(echo "${beta}" | tr -d ' ')"
  beta_tag="$(echo "${beta_trimmed}" | tr -d '.')"
  run_tag="small_real_dpo_ablation_beta${beta_tag}"

  echo "[dpo-ablation] run beta=${beta_trimmed} tag=${run_tag}"
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "${PYTHON_BIN}" src/train/real_dpo_train.py \
    --task "${run_tag}" \
    --pref-file "${PREF_FILE}" \
    --model-name "${MODEL_NAME}" \
    --output-dir "checkpoints/alignment/${run_tag}" \
    --logging-dir "logs/alignment/${run_tag}" \
    --metrics-out "reports/training/${run_tag}_metrics.json" \
    --epochs "${EPOCHS}" \
    --max-steps "${MAX_STEPS}" \
    --learning-rate "${LR:-1e-5}" \
    --weight-decay "${WEIGHT_DECAY:-0.0}" \
    --beta "${beta_trimmed}" \
    --max-length "${MAX_LENGTH}" \
    --seed "${SEED}" \
    --trust-remote-code false \
    --local-files-only true
done

echo "[dpo-ablation] step2 build report"
"${PYTHON_BIN}" scripts/audit/build_dpo_ablation_report.py
echo "[dpo-ablation] done"
