#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"
MODEL_TIER="${MODEL_TIER:-7b}" # 7b | 14b | auto
ALIGNMENT_MODE="${ALIGNMENT_MODE:-real}"
ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING:-false}"
FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING:-false}"

BUILD_REAL_DATA="${BUILD_REAL_DATA:-false}"
RUN_E2E="${RUN_E2E:-true}"
ALLOW_DEFERRED_READINESS="${ALLOW_DEFERRED_READINESS:-false}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-false}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-120}"
JUDGE_CACHE="${JUDGE_CACHE:-reports/eval/judge_cache.jsonl}"
ENABLE_LLM_RISK_JUDGE="${ENABLE_LLM_RISK_JUDGE:-true}"
LLM_RISK_MODEL="${LLM_RISK_MODEL:-gpt-4o-mini}"
LLM_RISK_MAX_SAMPLES="${LLM_RISK_MAX_SAMPLES:-200}"
LLM_RISK_CACHE="${LLM_RISK_CACHE:-reports/eval/judge_risk_cache.jsonl}"
ENABLE_V2_LLM_FALLBACK="${ENABLE_V2_LLM_FALLBACK:-true}"
V2_LLM_MODEL="${V2_LLM_MODEL:-gpt-4o-mini}"
V2_LLM_CACHE="${V2_LLM_CACHE:-reports/eval/judge_risk_cache_v2.jsonl}"
V2_LLM_MIN_CONF="${V2_LLM_MIN_CONF:-0.70}"
V2_LLM_MAX_CALLS="${V2_LLM_MAX_CALLS:-1200}"

EVAL_SPLITS="${EVAL_SPLITS:-validation,test}"
DET_MAX="${DET_MAX:-0}"
EVAL_MAX="${EVAL_MAX:-1200}"
SOTA_MAX="${SOTA_MAX:-1800}"
LOG_EVERY="${LOG_EVERY:-300}"
KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}"

MIGRATION_STATUS="${MIGRATION_STATUS:-reports/migration/gpu_run_status.md}"
DRY_RUN="${DRY_RUN:-false}"

echo "[gpu-run] model=${MODEL_NAME} tier=${MODEL_TIER} mode=${ALIGNMENT_MODE}"
echo "[gpu-run] allow_skip_training=${ALLOW_SKIP_TRAINING} force_skip_training=${FORCE_SKIP_TRAINING} dry_run=${DRY_RUN}"

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "[gpu-run] dry-run commands:"
  echo "  1) bash scripts/train/run_real_alignment_pipeline.sh"
  echo "  2) bash scripts/eval/run_thesis_pipeline.sh"
  echo "  3) python3 scripts/deploy/run_e2e_acceptance.py (optional)"
  echo "  4) python3 scripts/audit/check_thesis_readiness.py"
  echo "  5) python3 scripts/migration/check_gpu_completion.py"
  exit 0
fi

api_required=false
if [[ "${ENABLE_LLM_JUDGE}" == "true" ]] || [[ "${ENABLE_LLM_RISK_JUDGE}" == "true" ]] || [[ "${ENABLE_V2_LLM_FALLBACK}" == "true" ]]; then
  api_required=true
fi

if [[ "${api_required}" == "true" ]]; then
  if [[ ! -f ".env" && -z "${OPENAI_API_KEY:-}" ]]; then
    echo "[gpu-run] API evaluation enabled but .env and OPENAI_API_KEY are missing."
    echo "[gpu-run] either provide .env or set ENABLE_LLM_JUDGE/ENABLE_LLM_RISK_JUDGE/ENABLE_V2_LLM_FALLBACK=false"
    exit 1
  fi
fi

python - <<'PY'
import json
try:
    import torch
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"[gpu-run] torch unavailable: {exc}")
if not torch.cuda.is_available():
    raise SystemExit("[gpu-run] CUDA not available. Abort to avoid fake real-training run.")
total = 0.0
for i in range(torch.cuda.device_count()):
    total += float(torch.cuda.get_device_properties(i).total_memory) / (1024**3)
print("[gpu-run] cuda_probe", json.dumps({"cuda_device_count": torch.cuda.device_count(), "cuda_total_mem_gb": round(total, 2)}))
PY

# 1) Real alignment training
ALIGNMENT_MODE="${ALIGNMENT_MODE}" \
MODEL_NAME="${MODEL_NAME}" \
MODEL_TIER="${MODEL_TIER}" \
ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING}" \
FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING}" \
bash scripts/train/run_real_alignment_pipeline.sh

# 2) Thesis evaluation stack
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
JUDGE_MODEL="${JUDGE_MODEL}" \
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES}" \
JUDGE_CACHE="${JUDGE_CACHE}" \
ENABLE_LLM_RISK_JUDGE="${ENABLE_LLM_RISK_JUDGE}" \
LLM_RISK_MODEL="${LLM_RISK_MODEL}" \
LLM_RISK_MAX_SAMPLES="${LLM_RISK_MAX_SAMPLES}" \
LLM_RISK_CACHE="${LLM_RISK_CACHE}" \
ENABLE_V2_LLM_FALLBACK="${ENABLE_V2_LLM_FALLBACK}" \
V2_LLM_MODEL="${V2_LLM_MODEL}" \
V2_LLM_CACHE="${V2_LLM_CACHE}" \
V2_LLM_MIN_CONF="${V2_LLM_MIN_CONF}" \
V2_LLM_MAX_CALLS="${V2_LLM_MAX_CALLS}" \
KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS}" \
EVAL_SPLITS="${EVAL_SPLITS}" \
DET_MAX="${DET_MAX}" \
EVAL_MAX="${EVAL_MAX}" \
SOTA_MAX="${SOTA_MAX}" \
LOG_EVERY="${LOG_EVERY}" \
bash scripts/eval/run_thesis_pipeline.sh

# 3) Optional e2e acceptance
if [[ "${RUN_E2E}" == "true" ]]; then
  python3 scripts/deploy/run_e2e_acceptance.py
fi

python3 scripts/audit/check_thesis_readiness.py \
  --report reports/thesis_support/thesis_readiness.md \
  --json reports/thesis_support/thesis_readiness.json

completion_cmd=(
  python3 scripts/migration/check_gpu_completion.py
  --thesis-readiness-json reports/thesis_support/thesis_readiness.json
  --report reports/migration/gpu_completion_check.md
  --json reports/migration/gpu_completion_check.json
)
if [[ "${ALLOW_DEFERRED_READINESS}" == "true" ]]; then
  completion_cmd+=(--allow-deferred)
fi
"${completion_cmd[@]}"

mkdir -p "$(dirname "${MIGRATION_STATUS}")"
cat > "${MIGRATION_STATUS}" <<EOF
# GPU Experiment Run Status

- Time (UTC): $(date -u +"%Y-%m-%dT%H:%M:%SZ")
- Model: \`${MODEL_NAME}\`
- Tier: \`${MODEL_TIER}\`
- Alignment mode: \`${ALIGNMENT_MODE}\`
- Allow skip training: \`${ALLOW_SKIP_TRAINING}\`

## Outputs
- \`reports/training/layer_b_qwen25_7b_sft_metrics.json\`
- \`reports/training/dpo_metrics.json\`
- \`reports/training/simpo_metrics.json\`
- \`reports/training/kto_metrics.json\`
- \`reports/eval_default.md\`
- \`reports/detection_eval.md\`
- \`reports/detection_eval_v2_balanced.md\`
- \`reports/detection_eval_v2_hybrid_llm.md\` (if enabled)
- \`reports/detection_eval_llm_judge.md\` (if enabled)
- \`reports/sota_compare.md\`
- \`reports/thesis_support/thesis_readiness.md\`
- \`reports/migration/gpu_completion_check.md\`
EOF

echo "[gpu-run] done status=${MIGRATION_STATUS}"
