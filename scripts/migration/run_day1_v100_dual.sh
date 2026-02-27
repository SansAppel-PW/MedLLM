#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

TEMPLATE_FILE="${TEMPLATE_FILE:-configs/runtime/v100_dual_32g.env}"

if [[ ! -f "${TEMPLATE_FILE}" ]]; then
  echo "[v100-day1] template not found: ${TEMPLATE_FILE}"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${TEMPLATE_FILE}"
set +a

mkdir -p "${HF_HOME:-/root/autodl-tmp/hf}" "${HUGGINGFACE_HUB_CACHE:-/root/autodl-tmp/hf/hub}" "${TRANSFORMERS_CACHE:-/root/autodl-tmp/hf/transformers}"

echo "[v100-day1] loaded template: ${TEMPLATE_FILE}"
echo "[v100-day1] model=${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct} tier=${MODEL_TIER:-7b}"
echo "[v100-day1] cuda_visible_devices=${CUDA_VISIBLE_DEVICES:-<unset>}"
echo "[v100-day1] bf16=${BF16:-<unset>} fp16=${FP16:-<unset>} align_bf16=${ALIGN_BF16:-<unset>} align_fp16=${ALIGN_FP16:-<unset>}"

bash day1_run.sh
