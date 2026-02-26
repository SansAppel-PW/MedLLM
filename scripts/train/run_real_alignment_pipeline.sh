#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
PREF_FILE="${PREF_FILE:-data/clean/real_pref_seed_pairs.jsonl}"
KB_FILE="${KB_FILE:-data/kg/real_medqa_reference_kb.jsonl}"
ALIGNMENT_MODE="${ALIGNMENT_MODE:-real}"  # proxy | real
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"
MODEL_TIER="${MODEL_TIER:-auto}"          # auto | small | 7b | 14b

ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING:-true}"
FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING:-false}"
MIN_CUDA_MEM_GB_7B="${MIN_CUDA_MEM_GB_7B:-18}"
MIN_CUDA_MEM_GB_14B="${MIN_CUDA_MEM_GB_14B:-36}"
RESOURCE_REPORT="${RESOURCE_REPORT:-reports/training/resource_preflight.json}"
RESOURCE_SKIP_REPORT="${RESOURCE_SKIP_REPORT:-reports/training/resource_skip_report.md}"

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

metrics_dpo="reports/training/dpo_metrics.json"
metrics_simpo="reports/training/simpo_metrics.json"
metrics_kto="reports/training/kto_metrics.json"

TRAINING_SKIPPED=false
SKIP_REASON=""

derive_model_tier() {
  if [[ "${MODEL_TIER}" != "auto" ]]; then
    echo "${MODEL_TIER}"
    return 0
  fi
  local name_lower
  name_lower="$(echo "${MODEL_NAME}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${name_lower}" == *"14b"* ]]; then
    echo "14b"
  elif [[ "${name_lower}" == *"7b"* || "${name_lower}" == *"8b"* ]]; then
    echo "7b"
  else
    echo "small"
  fi
}

probe_resources() {
  mkdir -p "$(dirname "${RESOURCE_REPORT}")"
  python3 - "${RESOURCE_REPORT}" <<'PY'
import json
import platform
import sys
from datetime import datetime, timezone

report_path = sys.argv[1]
payload = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "platform": platform.platform(),
    "accelerator": "cpu",
    "cuda_device_count": 0,
    "cuda_total_mem_gb": 0.0,
}
try:
    import torch  # type: ignore

    if torch.cuda.is_available():
        payload["accelerator"] = "cuda"
        payload["cuda_device_count"] = int(torch.cuda.device_count())
        total = 0.0
        for i in range(torch.cuda.device_count()):
            total += float(torch.cuda.get_device_properties(i).total_memory) / (1024**3)
        payload["cuda_total_mem_gb"] = round(total, 2)
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        payload["accelerator"] = "mps"
except Exception as exc:  # noqa: BLE001
    payload["probe_error"] = str(exc)

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(payload["accelerator"], payload["cuda_total_mem_gb"], payload["cuda_device_count"])
PY
}

write_skipped_metric() {
  local method="$1"
  local path="$2"
  local reason="$3"
  mkdir -p "$(dirname "${path}")"
  python3 - "${method}" "${path}" "${reason}" <<'PY'
import json
import sys
from datetime import datetime, timezone

method, out_path, reason = sys.argv[1], sys.argv[2], sys.argv[3]
payload = {
    "method": method,
    "simulation": False,
    "skipped": True,
    "skip_reason": reason,
    "samples": 0,
    "global_steps": 0,
    "avg_loss": None,
    "avg_delta": None,
    "base_score": 0.0,
    "aligned_score": 0.0,
    "score_gain": 0.0,
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
PY
}

write_sft_skipped_metric() {
  local path="$1"
  local reason="$2"
  mkdir -p "$(dirname "${path}")"
  python3 - "${path}" "${reason}" <<'PY'
import json
import sys
from datetime import datetime, timezone

out_path, reason = sys.argv[1], sys.argv[2]
payload = {
    "skipped": True,
    "skip_reason": reason,
    "train_runtime": 0.0,
    "train_samples_per_second": 0.0,
    "train_steps_per_second": 0.0,
    "train_loss": None,
    "final_eval_loss": None,
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
PY
}

write_skip_report() {
  local reason="$1"
  mkdir -p "$(dirname "${RESOURCE_SKIP_REPORT}")"
  cat > "${RESOURCE_SKIP_REPORT}" <<EOF
# 训练跳过报告

- 时间: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- 模型: \`${MODEL_NAME}\`
- 模型层级: \`${MODEL_TIER_DERIVED}\`
- 跳过原因: ${reason}
- 资源探测: \`${RESOURCE_REPORT}\`

## 后续动作
1. 扩容到可用 CUDA 显存后，重新运行：
   \`ALIGNMENT_MODE=real MODEL_NAME=${MODEL_NAME} bash scripts/train/run_real_alignment_pipeline.sh\`
2. 当前其余模块可继续执行，不阻塞评测与论文素材构建。
EOF
}

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
      --num-workers "${ALIGN_NUM_WORKERS:-0}" \
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

MODEL_TIER_DERIVED="$(derive_model_tier)"
read -r ACCELERATOR TOTAL_MEM_GB CUDA_COUNT < <(probe_resources)
echo "[resource] accelerator=${ACCELERATOR} cuda_mem_gb=${TOTAL_MEM_GB} cuda_count=${CUDA_COUNT} model_tier=${MODEL_TIER_DERIVED}"

if [[ "${FORCE_SKIP_TRAINING}" == "true" ]]; then
  TRAINING_SKIPPED=true
  SKIP_REASON="FORCE_SKIP_TRAINING=true"
fi

if [[ "${TRAINING_SKIPPED}" == "false" ]]; then
  if [[ "${MODEL_TIER_DERIVED}" == "14b" ]]; then
    if [[ "${ACCELERATOR}" != "cuda" ]] || ! python3 - <<PY
mem = float("${TOTAL_MEM_GB}")
need = float("${MIN_CUDA_MEM_GB_14B}")
raise SystemExit(0 if mem >= need else 1)
PY
    then
      TRAINING_SKIPPED=true
      SKIP_REASON="Insufficient CUDA resources for 14B (need >= ${MIN_CUDA_MEM_GB_14B}GB)."
    fi
  elif [[ "${MODEL_TIER_DERIVED}" == "7b" ]]; then
    if [[ "${ACCELERATOR}" != "cuda" ]] || ! python3 - <<PY
mem = float("${TOTAL_MEM_GB}")
need = float("${MIN_CUDA_MEM_GB_7B}")
raise SystemExit(0 if mem >= need else 1)
PY
    then
      TRAINING_SKIPPED=true
      SKIP_REASON="Insufficient CUDA resources for 7B (need >= ${MIN_CUDA_MEM_GB_7B}GB)."
    fi
  fi
fi

if [[ "${TRAINING_SKIPPED}" == "true" && "${ALLOW_SKIP_TRAINING}" != "true" ]]; then
  echo "[error] ${SKIP_REASON}"
  exit 1
fi

# Step 1: build preference pairs (independent of model training)
python3 src/train/hard_negative_builder.py \
  --input "${TRAIN_FILE}" \
  --kg "${KB_FILE}" \
  --output "${PREF_FILE}"

if [[ "${TRAINING_SKIPPED}" == "true" ]]; then
  echo "[warn] training skipped: ${SKIP_REASON}"
  write_skip_report "${SKIP_REASON}"
  write_sft_skipped_metric "${SFT_METRICS_OUT}" "${SKIP_REASON}"
  write_skipped_metric "DPO" "${metrics_dpo}" "${SKIP_REASON}"
  write_skipped_metric "SimPO" "${metrics_simpo}" "${SKIP_REASON}"
  write_skipped_metric "KTO" "${metrics_kto}" "${SKIP_REASON}"
else
  # Step 2: real SFT (Layer-B baseline)
  set +e
  TRAIN_FILE="${TRAIN_FILE}" \
  DEV_FILE="${DEV_FILE}" \
  MODEL_NAME="${MODEL_NAME}" \
  OUTPUT_DIR="${SFT_OUTPUT_DIR}" \
  LOGGING_DIR="${SFT_LOGGING_DIR}" \
  METRICS_OUT="${SFT_METRICS_OUT}" \
  bash scripts/train/run_layer_b_real_sft.sh
  sft_rc=$?
  set -e
  if [[ ${sft_rc} -ne 0 ]]; then
    if [[ "${ALLOW_SKIP_TRAINING}" == "true" ]]; then
      TRAINING_SKIPPED=true
      SKIP_REASON="SFT failed and fallback enabled (rc=${sft_rc})."
      echo "[warn] ${SKIP_REASON}"
      write_skip_report "${SKIP_REASON}"
      write_sft_skipped_metric "${SFT_METRICS_OUT}" "${SKIP_REASON}"
      write_skipped_metric "DPO" "${metrics_dpo}" "${SKIP_REASON}"
      write_skipped_metric "SimPO" "${metrics_simpo}" "${SKIP_REASON}"
      write_skipped_metric "KTO" "${metrics_kto}" "${SKIP_REASON}"
    else
      exit "${sft_rc}"
    fi
  fi
fi

if [[ "${TRAINING_SKIPPED}" == "false" ]]; then
  if [[ "${ALIGNMENT_MODE}" == "proxy" ]]; then
    echo "[warn] ALIGNMENT_MODE=proxy: DPO/SimPO/KTO will run simulated trainers."

    python3 src/train/dpo_train.py \
      --pref-file "${PREF_FILE}" \
      --output-dir checkpoints/dpo-real-baseline \
      --metrics-out "${metrics_dpo}"

    python3 src/train/simpo_train.py \
      --pref-file "${PREF_FILE}" \
      --output-dir checkpoints/simpo-real-baseline \
      --metrics-out "${metrics_simpo}"

    python3 src/train/kto_train.py \
      --pref-file "${PREF_FILE}" \
      --output-dir checkpoints/kto-real-baseline \
      --metrics-out "${metrics_kto}"
  elif [[ "${ALIGNMENT_MODE}" == "real" ]]; then
    if ! run_real_pref_with_retry \
      dpo \
      configs/train/dpo_real.yaml \
      checkpoints/dpo-real-baseline \
      logs/dpo-real-baseline \
      "${metrics_dpo}"; then
      if [[ "${ALLOW_SKIP_TRAINING}" == "true" ]]; then
        write_skipped_metric "DPO" "${metrics_dpo}" "DPO training failed after retries."
      else
        exit 1
      fi
    fi

    if ! run_real_pref_with_retry \
      simpo \
      configs/train/simpo_real.yaml \
      checkpoints/simpo-real-baseline \
      logs/simpo-real-baseline \
      "${metrics_simpo}"; then
      if [[ "${ALLOW_SKIP_TRAINING}" == "true" ]]; then
        write_skipped_metric "SimPO" "${metrics_simpo}" "SimPO training failed after retries."
      else
        exit 1
      fi
    fi

    if ! run_real_pref_with_retry \
      kto \
      configs/train/kto_real.yaml \
      checkpoints/kto-real-baseline \
      logs/kto-real-baseline \
      "${metrics_kto}"; then
      if [[ "${ALLOW_SKIP_TRAINING}" == "true" ]]; then
        write_skipped_metric "KTO" "${metrics_kto}" "KTO training failed after retries."
      else
        exit 1
      fi
    fi
  else
    echo "[error] ALIGNMENT_MODE must be one of: proxy, real"
    exit 1
  fi
fi

python3 src/train/compare_alignment.py \
  --dpo "${metrics_dpo}" \
  --simpo "${metrics_simpo}" \
  --kto "${metrics_kto}" \
  --output reports/alignment_compare.md

echo "[real-alignment-pipeline] done mode=${ALIGNMENT_MODE} skipped=${TRAINING_SKIPPED}"
