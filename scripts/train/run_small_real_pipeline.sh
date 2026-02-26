#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
SEED="${SEED:-42}"
RUN_TAG="${RUN_TAG:-small_real_lora_v3}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/sft_dev.jsonl}"
OUTPUT_DIR="${OUTPUT_DIR:-checkpoints/small_real/${RUN_TAG}}"
LOGGING_DIR="${LOGGING_DIR:-logs/small_real/${RUN_TAG}}"
TRAIN_METRICS="${TRAIN_METRICS:-reports/training/${RUN_TAG}_metrics.json}"

EVAL_DIR="${EVAL_DIR:-reports/small_real/${RUN_TAG}}"
PRED_OUT="${PRED_OUT:-${EVAL_DIR}/predictions.jsonl}"
EVAL_JSON="${EVAL_JSON:-${EVAL_DIR}/eval_metrics.json}"
EVAL_CSV="${EVAL_CSV:-${EVAL_DIR}/eval_metrics.csv}"
EVAL_MD="${EVAL_MD:-${EVAL_DIR}/eval_report.md}"
LOSS_CSV="${LOSS_CSV:-${EVAL_DIR}/loss_curve.csv}"
LOSS_PNG="${LOSS_PNG:-${EVAL_DIR}/loss_curve.png}"
LOSS_PDF="${LOSS_PDF:-${EVAL_DIR}/loss_curve.pdf}"
RUN_CARD_JSON="${RUN_CARD_JSON:-${EVAL_DIR}/run_card.json}"
RUN_CARD_MD="${RUN_CARD_MD:-${EVAL_DIR}/run_card.md}"

MODEL_PRIMARY="${MODEL_PRIMARY:-Qwen/Qwen2.5-0.5B-Instruct}"
MODEL_FALLBACK="${MODEL_FALLBACK:-${HOME}/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be}"

PRIMARY_TARGETS="${PRIMARY_TARGETS:-q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj}"
FALLBACK_TARGETS="${FALLBACK_TARGETS:-c_attn,c_proj}"

mkdir -p "$(dirname "${TRAIN_METRICS}")" "${EVAL_DIR}"

echo "[small-real] step1 prepare_data"
"${PYTHON_BIN}" scripts/data/run_data_governance_pipeline.py --seed "${SEED}"

run_train() {
  local model_name="$1"
  local lora_targets="$2"
  local trust_remote_code="$3"
  local local_files_only="$4"
  local offline="$5"
  local timeout_sec="${6:-0}"
  local -a extra_env=()
  if [[ "${offline}" == "1" ]]; then
    extra_env+=(HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1)
  fi

  echo "[small-real] train model=${model_name} local_files_only=${local_files_only}"
  local -a train_cmd=(
    "${PYTHON_BIN}" src/train/real_sft_train.py
    --task small_real_pipeline
    --config configs/train/sft_real.yaml
    --train-file "${TRAIN_FILE}"
    --dev-file "${DEV_FILE}"
    --model-name "${model_name}"
    --output-dir "${OUTPUT_DIR}"
    --logging-dir "${LOGGING_DIR}"
    --metrics-out "${TRAIN_METRICS}"
    --max-length "${MAX_LENGTH:-128}"
    --num-train-epochs "${NUM_EPOCHS:-3}"
    --max-steps "${MAX_STEPS:-8}"
    --learning-rate "${LR:-2e-4}"
    --weight-decay "${WEIGHT_DECAY:-0.0}"
    --warmup-ratio "${WARMUP_RATIO:-0.0}"
    --optim "${OPTIM:-adamw_torch}"
    --per-device-train-batch-size "${TRAIN_BSZ:-1}"
    --per-device-eval-batch-size "${EVAL_BSZ:-1}"
    --gradient-accumulation-steps "${GRAD_ACC:-1}"
    --gradient-checkpointing "${GRAD_CKPT:-false}"
    --num-workers "${NUM_WORKERS:-0}"
    --logging-steps "${LOG_STEPS:-1}"
    --save-steps "${SAVE_STEPS:-2}"
    --eval-steps "${EVAL_STEPS:-2}"
    --save-total-limit "${SAVE_LIMIT:-2}"
    --seed "${SEED}"
    --bf16 false
    --fp16 false
    --device-map-auto false
    --use-lora true
    --lora-r "${LORA_R:-8}"
    --lora-alpha "${LORA_ALPHA:-16}"
    --lora-dropout "${LORA_DROPOUT:-0.05}"
    --lora-target-modules "${lora_targets}"
    --load-in-4bit false
    --trust-remote-code "${trust_remote_code}"
    --local-files-only "${local_files_only}"
  )

  local -a final_cmd=()
  if [[ "${#extra_env[@]}" -gt 0 ]]; then
    final_cmd=(env "${extra_env[@]}" "${train_cmd[@]}")
  else
    final_cmd=("${train_cmd[@]}")
  fi

  if [[ "${timeout_sec}" -gt 0 ]]; then
    local -a timeout_cmd=("${final_cmd[@]}")
    (
      "${timeout_cmd[@]}" &
      local cmd_pid=$!
      (
        sleep "${timeout_sec}"
        if kill -0 "${cmd_pid}" 2>/dev/null; then
          echo "[small-real] timeout ${timeout_sec}s reached, terminate pid=${cmd_pid}"
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

echo "[small-real] step2 train"
PRIMARY_TIMEOUT="${PRIMARY_TIMEOUT:-300}"
if ! run_train "${MODEL_PRIMARY}" "${PRIMARY_TARGETS}" true false 0 "${PRIMARY_TIMEOUT}"; then
  echo "[small-real] primary model failed, trying fallback model: ${MODEL_FALLBACK}"
  if [[ ! -d "${MODEL_FALLBACK}" ]]; then
    echo "[small-real] fallback model path not found: ${MODEL_FALLBACK}" >&2
    exit 1
  fi
  run_train "${MODEL_FALLBACK}" "${FALLBACK_TARGETS}" false true 1 0
fi

echo "[small-real] step3 eval"
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "${PYTHON_BIN}" scripts/eval/run_small_real_eval.py \
  --model-dir "${OUTPUT_DIR}/final" \
  --input "${DEV_FILE}" \
  --pred-out "${PRED_OUT}" \
  --metrics-json "${EVAL_JSON}" \
  --metrics-csv "${EVAL_CSV}" \
  --report-md "${EVAL_MD}" \
  --max-new-tokens "${MAX_NEW_TOKENS:-64}"

echo "[small-real] step4 visualize"
"${PYTHON_BIN}" scripts/eval/plot_training_loss.py \
  --log-jsonl "${LOGGING_DIR}/train_log.jsonl" \
  --out-csv "${LOSS_CSV}" \
  --out-png "${LOSS_PNG}" \
  --out-pdf "${LOSS_PDF}"

echo "[small-real] step5 run_card"
"${PYTHON_BIN}" scripts/eval/build_small_real_run_card.py \
  --manifest "${OUTPUT_DIR}/run_manifest.json" \
  --train-metrics "${TRAIN_METRICS}" \
  --eval-metrics "${EVAL_JSON}" \
  --loss-csv "${LOSS_CSV}" \
  --loss-png "${LOSS_PNG}" \
  --predictions "${PRED_OUT}" \
  --out-json "${RUN_CARD_JSON}" \
  --out-md "${RUN_CARD_MD}"

echo "[small-real] done run_tag=${RUN_TAG}"
