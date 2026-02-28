#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"
USE_TORCHRUN="${USE_TORCHRUN:-0}"
NUM_GPUS="${NUM_GPUS:-1}"
TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
BASE_OUTPUT="${BASE_OUTPUT:-checkpoints/layer_b/qwen25_7b_qlora}"
BASE_LOG="${BASE_LOG:-logs/layer_b/qwen25_7b_qlora}"
METRICS_OUT="${METRICS_OUT:-reports/training/layer_b_qwen25_7b_qlora_metrics.json}"
METRICS_OUT_SFT_ALIAS="${METRICS_OUT_SFT_ALIAS:-reports/training/layer_b_qwen25_7b_sft_metrics.json}"
BLOCKER_REPORT="${BLOCKER_REPORT:-reports/small_real/qwen_layer_b_blocker.md}"
ATTEMPT_TIMEOUT_SEC="${ATTEMPT_TIMEOUT_SEC:-900}"
DEFAULT_MAX_STEPS="${DEFAULT_MAX_STEPS:-400}"
MIN_CACHE_FREE_MB="${MIN_CACHE_FREE_MB:-12288}"

mkdir -p "$(dirname "${BLOCKER_REPORT}")" "${BASE_LOG}" "$(dirname "${METRICS_OUT}")"
mkdir -p "$(dirname "${METRICS_OUT_SFT_ALIAS}")"

if [[ -z "${HF_HOME:-}" && -d "/root/autodl-tmp" && -w "/root/autodl-tmp" ]]; then
  export HF_HOME="/root/autodl-tmp/hf-cache"
fi
if [[ -n "${HF_HOME:-}" ]]; then
  export HF_HUB_CACHE="${HF_HUB_CACHE:-${HF_HOME}/hub}"
  export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-${HF_HOME}/transformers}"
  mkdir -p "${HF_HOME}" "${HF_HUB_CACHE}" "${TRANSFORMERS_CACHE}"
fi

write_blocker_report() {
  local reason="$1"
  local detail="$2"
  cat >"${BLOCKER_REPORT}" <<EOF
# Qwen7B Layer-B 阻塞报告

- 时间: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- 状态: ${reason}
- 影响: Layer-B 主实验（Qwen7B）训练阶段暂不可用，但其余闭环可继续执行。

## 详情
${detail}

## 建议
1. 优先使用数据盘缓存模型，设置 \`HF_HOME=/root/autodl-tmp/hf-cache\`。
2. 如为网络问题，可重试并切换镜像（\`HF_ENDPOINT\`）。
3. 如为算力或显存问题，继续使用自动降级策略并保留 blocker 报告用于论文说明。
EOF
}

model_cache_ready() {
  local base="${HF_HUB_CACHE:-$HOME/.cache/huggingface/hub}"
  local snap_dir="${base}/models--Qwen--Qwen2.5-7B-Instruct/snapshots"
  if [[ ! -d "${snap_dir}" ]]; then
    return 1
  fi
  find "${snap_dir}" -type l -name "*.safetensors" | grep -q .
}

check_cache_space() {
  local probe_dir="${HF_HUB_CACHE:-$HOME/.cache/huggingface/hub}"
  mkdir -p "${probe_dir}"
  local free_mb
  free_mb="$(df -Pm "${probe_dir}" | awk 'NR==2 {print $4}')"
  if [[ -z "${free_mb}" ]]; then
    return 0
  fi
  if (( free_mb < MIN_CACHE_FREE_MB )) && ! model_cache_ready; then
    local detail="HF cache directory free space is ${free_mb}MB (<${MIN_CACHE_FREE_MB}MB) and Qwen2.5-7B local cache is incomplete."
    echo "[qwen-layer-b] ${detail}"
    write_blocker_report "磁盘空间不足导致模型下载失败风险高" "${detail}"
    return 4
  fi
  return 0
}

if [[ -z "${BF16:-}" || -z "${FP16:-}" ]]; then
  bf16_capable="$("${PYTHON_BIN}" - <<'PY'
import torch
ok = bool(torch.cuda.is_available() and getattr(torch.cuda, "is_bf16_supported", lambda: False)())
print("1" if ok else "0")
PY
)"
  if [[ -z "${BF16:-}" ]]; then
    if [[ "${bf16_capable}" == "1" ]]; then
      BF16="true"
    else
      BF16="false"
    fi
  fi
  if [[ -z "${FP16:-}" ]]; then
    if [[ "${BF16}" == "true" ]]; then
      FP16="false"
    else
      FP16="true"
    fi
  fi
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  write_blocker_report \
    "当前环境无 nvidia-smi，无法执行 Qwen2.5-7B QLoRA 真实训练" \
    "可先完成其余模块（alignment/eval/report），迁移 GPU 后再重跑 Layer-B。"
  echo "[qwen-layer-b] no-gpu blocker report written: ${BLOCKER_REPORT}"
  exit 0
fi

if ! check_cache_space; then
  exit 4
fi

available_gpus="$(nvidia-smi --list-gpus | wc -l | tr -d '[:space:]')"
if [[ "${NUM_GPUS}" -gt "${available_gpus}" ]]; then
  echo "[qwen-layer-b] requested NUM_GPUS=${NUM_GPUS} > available=${available_gpus}, clamp to available."
  NUM_GPUS="${available_gpus}"
fi

if [[ "${USE_TORCHRUN}" == "1" && "${NUM_GPUS}" -gt 1 ]]; then
  LAUNCHER=("${PYTHON_BIN}" -m torch.distributed.run --standalone --nnodes=1 --nproc_per_node "${NUM_GPUS}")
  DEVICE_MAP_AUTO="${DEVICE_MAP_AUTO:-false}"
  echo "[qwen-layer-b] launcher=torchrun nproc_per_node=${NUM_GPUS}"
else
  LAUNCHER=("${PYTHON_BIN}")
  DEVICE_MAP_AUTO="${DEVICE_MAP_AUTO:-true}"
  echo "[qwen-layer-b] launcher=single-process"
fi

sync_layer_b_metrics() {
  if [[ -f "${METRICS_OUT}" && "${METRICS_OUT}" != "${METRICS_OUT_SFT_ALIAS}" ]]; then
    cp "${METRICS_OUT}" "${METRICS_OUT_SFT_ALIAS}"
  elif [[ -f "${METRICS_OUT_SFT_ALIAS}" && "${METRICS_OUT}" != "${METRICS_OUT_SFT_ALIAS}" ]]; then
    cp "${METRICS_OUT_SFT_ALIAS}" "${METRICS_OUT}"
  fi
}

try_train() {
  local attempt="$1"
  local max_len="$2"
  local grad_acc="$3"
  local out_dir="${BASE_OUTPUT}_attempt${attempt}"
  local log_dir="${BASE_LOG}_attempt${attempt}"
  local run_log="${log_dir}/attempt.log"
  mkdir -p "${log_dir}"

  echo "[qwen-layer-b] attempt=${attempt} max_len=${max_len} grad_acc=${grad_acc} bf16=${BF16} fp16=${FP16} device_map_auto=${DEVICE_MAP_AUTO}"
  local cmd=(
    "${LAUNCHER[@]}" src/train/real_sft_train.py
    --task "layer_b_qwen7b_attempt${attempt}"
    --config configs/train/sft_layer_b_qwen7b_qlora.yaml
    --model-name "${MODEL_NAME}"
    --train-file "${TRAIN_FILE}"
    --dev-file "${DEV_FILE}"
    --output-dir "${out_dir}"
    --logging-dir "${log_dir}"
    --metrics-out "${METRICS_OUT}"
    --max-length "${max_len}"
    --num-train-epochs "${NUM_EPOCHS:-1}"
    --max-steps "${MAX_STEPS:-${DEFAULT_MAX_STEPS}}"
    --learning-rate 2e-5
    --weight-decay 0.01
    --warmup-ratio 0.03
    --optim paged_adamw_8bit
    --per-device-train-batch-size 1
    --per-device-eval-batch-size 1
    --gradient-accumulation-steps "${grad_acc}"
    --gradient-checkpointing true
    --num-workers 2
    --logging-steps 10
    --save-steps 100
    --eval-steps 100
    --save-total-limit 3
    --seed 42
    --bf16 "${BF16}"
    --fp16 "${FP16}"
    --device-map-auto "${DEVICE_MAP_AUTO}"
    --use-lora true
    --lora-r 64
    --lora-alpha 128
    --lora-dropout 0.05
    --lora-target-modules q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj
    --load-in-4bit true
    --bnb-4bit-quant-type nf4
    --bnb-4bit-use-double-quant true
    --trust-remote-code true
  )
  local rc=0
  if [[ "${ATTEMPT_TIMEOUT_SEC}" -gt 0 ]] && command -v timeout >/dev/null 2>&1; then
    if timeout "${ATTEMPT_TIMEOUT_SEC}" "${cmd[@]}" >"${run_log}" 2>&1; then
      rc=0
    else
      rc=$?
    fi
  else
    if "${cmd[@]}" >"${run_log}" 2>&1; then
      rc=0
    else
      rc=$?
    fi
  fi

  if [[ ${rc} -eq 0 ]]; then
    sync_layer_b_metrics
    echo "[qwen-layer-b] success attempt=${attempt}"
    return 0
  fi

  if [[ ${rc} -eq 124 ]]; then
    echo "[qwen-layer-b] attempt=${attempt} timed out (${ATTEMPT_TIMEOUT_SEC}s), trying fallback..."
    return 3
  fi

  if grep -Eqi "Not enough free disk space|No space left on device" "${run_log}"; then
    echo "[qwen-layer-b] cache/disk issue detected on attempt=${attempt}."
    return 4
  fi

  if grep -Eqi "ReadTimeout|Connection timed out|Max retries exceeded|Temporary failure in name resolution|Failed to download|ConnectionError" "${run_log}"; then
    echo "[qwen-layer-b] network/download issue detected on attempt=${attempt}."
    return 5
  fi

  if grep -Eqi "out of memory|cuda out of memory|cublas|resource exhausted" "${run_log}"; then
    echo "[qwen-layer-b] OOM detected on attempt=${attempt}, trying fallback..."
    return 2
  fi

  if grep -Eqi "TCPStore|socket\\.cpp|client socket has timed out|Name or service not known|c10d|torch\\.distributed\\.elastic\\.multiprocessing\\.errors\\.ChildFailedError" "${run_log}"; then
    echo "[qwen-layer-b] distributed bootstrap failure on attempt=${attempt}, trying single-process fallback..."
    return 3
  fi

  echo "[qwen-layer-b] non-OOM failure on attempt=${attempt}, see ${run_log}"
  return 1
}

set +e
try_train 1 2048 16
rc=$?
set -e
if [[ ${rc} -eq 0 ]]; then
  exit 0
fi

if [[ ${rc} -eq 3 ]]; then
  echo "[qwen-layer-b] auto-downgrade to single-process because distributed bootstrap failed."
  USE_TORCHRUN=0
  NUM_GPUS=1
  LAUNCHER=("${PYTHON_BIN}")
  DEVICE_MAP_AUTO=true
  set +e
  try_train 11 1536 32
  rc=$?
  set -e
  if [[ ${rc} -eq 0 ]]; then
    exit 0
  fi
  if [[ ${rc} -eq 2 ]]; then
    set +e
    try_train 12 1024 64
    rc=$?
    set -e
    if [[ ${rc} -eq 0 ]]; then
      exit 0
    fi
  fi
  if [[ ${rc} -eq 2 ]]; then
    set +e
    try_train 13 768 96
    rc=$?
    set -e
    if [[ ${rc} -eq 0 ]]; then
      exit 0
    fi
  fi
fi

if [[ ${rc} -eq 2 ]]; then
  set +e
  try_train 2 1536 32
  rc=$?
  set -e
  if [[ ${rc} -eq 0 ]]; then
    exit 0
  fi
fi
if [[ ${rc} -eq 2 ]]; then
  set +e
  try_train 3 1024 64
  rc=$?
  set -e
  if [[ ${rc} -eq 0 ]]; then
    exit 0
  fi
fi

case "${rc}" in
  4)
    write_blocker_report "缓存空间不足或写盘失败" "请检查 HF cache 所在分区剩余空间，并设置 HF_HOME 到数据盘。"
    ;;
  5)
    write_blocker_report "模型下载网络不稳定" "请重试，或切换网络镜像后再运行 Layer-B。"
    ;;
  *)
    write_blocker_report "Layer-B 训练失败" "请检查 logs/layer_b/*/attempt.log 获取详细错误。"
    ;;
esac

echo "[qwen-layer-b] all attempts failed (rc=${rc})"
exit "${rc}"
