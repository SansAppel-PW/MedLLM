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
BLOCKER_REPORT="${BLOCKER_REPORT:-reports/small_real/qwen_layer_b_blocker.md}"

mkdir -p "$(dirname "${BLOCKER_REPORT}")" "${BASE_LOG}" "$(dirname "${METRICS_OUT}")"

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
  cat >"${BLOCKER_REPORT}" <<EOF
# Qwen7B Layer-B 阻塞报告

- 时间: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- 状态: 当前环境无 \`nvidia-smi\`，无法执行 Qwen2.5-7B QLoRA 真实训练。
- 影响: Layer-B 主实验（Qwen7B）训练阶段被阻塞，但小规模真实闭环已完成，可作为迁移前验证层。

## 建议迁移配置
- 模型: \`${MODEL_NAME}\`
- 训练文件: \`${TRAIN_FILE}\`
- 验证文件: \`${DEV_FILE}\`
- 推荐最小显存: >= 24GB (QLoRA 4bit, bs=1, grad_acc>=16)
- 启动命令:
\`\`\`bash
bash scripts/train/run_layer_b_qwen_autofallback.sh
\`\`\`
- V100 推荐:
\`\`\`bash
USE_TORCHRUN=1 NUM_GPUS=2 BF16=false FP16=true bash scripts/train/run_layer_b_qwen_autofallback.sh
\`\`\`

## 自愈策略
1. 首次尝试: max_length=2048, grad_acc=16
2. OOM 回退1: max_length=1536, grad_acc=32
3. OOM 回退2: max_length=1024, grad_acc=64
EOF
  echo "[qwen-layer-b] no-gpu blocker report written: ${BLOCKER_REPORT}"
  exit 0
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

try_train() {
  local attempt="$1"
  local max_len="$2"
  local grad_acc="$3"
  local out_dir="${BASE_OUTPUT}_attempt${attempt}"
  local log_dir="${BASE_LOG}_attempt${attempt}"
  local run_log="${log_dir}/attempt.log"
  mkdir -p "${log_dir}"

  echo "[qwen-layer-b] attempt=${attempt} max_len=${max_len} grad_acc=${grad_acc} bf16=${BF16} fp16=${FP16} device_map_auto=${DEVICE_MAP_AUTO}"
  set +e
  "${LAUNCHER[@]}" src/train/real_sft_train.py \
    --task "layer_b_qwen7b_attempt${attempt}" \
    --config configs/train/sft_layer_b_qwen7b_qlora.yaml \
    --model-name "${MODEL_NAME}" \
    --train-file "${TRAIN_FILE}" \
    --dev-file "${DEV_FILE}" \
    --output-dir "${out_dir}" \
    --logging-dir "${log_dir}" \
    --metrics-out "${METRICS_OUT}" \
    --max-length "${max_len}" \
    --num-train-epochs 1 \
    --max-steps -1 \
    --learning-rate 2e-5 \
    --weight-decay 0.01 \
    --warmup-ratio 0.03 \
    --optim paged_adamw_8bit \
    --per-device-train-batch-size 1 \
    --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps "${grad_acc}" \
    --gradient-checkpointing true \
    --num-workers 2 \
    --logging-steps 10 \
    --save-steps 100 \
    --eval-steps 100 \
    --save-total-limit 3 \
    --seed 42 \
    --bf16 "${BF16}" \
    --fp16 "${FP16}" \
    --device-map-auto "${DEVICE_MAP_AUTO}" \
    --use-lora true \
    --lora-r 64 \
    --lora-alpha 128 \
    --lora-dropout 0.05 \
    --lora-target-modules q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj \
    --load-in-4bit true \
    --bnb-4bit-quant-type nf4 \
    --bnb-4bit-use-double-quant true \
    --trust-remote-code true \
    >"${run_log}" 2>&1
  local rc=$?
  set -e

  if [[ ${rc} -eq 0 ]]; then
    echo "[qwen-layer-b] success attempt=${attempt}"
    return 0
  fi

  if grep -Eqi "out of memory|cuda out of memory|cublas|resource exhausted" "${run_log}"; then
    echo "[qwen-layer-b] OOM detected on attempt=${attempt}, trying fallback..."
    return 2
  fi

  echo "[qwen-layer-b] non-OOM failure on attempt=${attempt}, see ${run_log}"
  return 1
}

if try_train 1 2048 16; then
  exit 0
fi
rc=$?
if [[ ${rc} -eq 2 ]]; then
  if try_train 2 1536 32; then
    exit 0
  fi
  rc=$?
fi
if [[ ${rc} -eq 2 ]]; then
  if try_train 3 1024 64; then
    exit 0
  fi
fi

echo "[qwen-layer-b] all attempts failed"
exit 1
