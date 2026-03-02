#!/usr/bin/env bash
set -euo pipefail

# One-shot GPU execution + artifact harvest bundle.
# Designed for expensive rental sessions: maximize outputs in one run.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

TS="${TS:-$(date +%Y%m%d_%H%M%S)}"
PYTHON_BIN="${PYTHON_BIN:-$( [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3 )}"
SESSION_LOG_DIR="${SESSION_LOG_DIR:-logs/session}"
mkdir -p "${SESSION_LOG_DIR}"
RUN_LOG="${SESSION_LOG_DIR}/gpu_once_harvest_${TS}.log"

NUM_GPUS="${NUM_GPUS:-2}"
USE_TORCHRUN="${USE_TORCHRUN:-1}"
BF16="${BF16:-false}"
FP16="${FP16:-true}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-0}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-240}"
ALLOW_LAYER_B_BLOCKER="${ALLOW_LAYER_B_BLOCKER:-1}"
HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
INCLUDE_LOGS_IN_BUNDLE="${INCLUDE_LOGS_IN_BUNDLE:-1}"
INCLUDE_CLEAN_DATA_IN_BUNDLE="${INCLUDE_CLEAN_DATA_IN_BUNDLE:-1}"
AUTO_SHUTDOWN="${AUTO_SHUTDOWN:-0}"

exec > >(tee -a "${RUN_LOG}") 2>&1

step() {
  echo
  echo "[$(date '+%F %T')] [GPU-ONCE] $*"
}

fail() {
  echo "[$(date '+%F %T')] [GPU-ONCE][ERROR] $*" >&2
  exit 1
}

step "Check branch and basic environment"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[[ "${BRANCH}" == "codex/worktree-gpt-prompt" ]] || fail "Wrong branch: ${BRANCH}"
command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi not found"
nvidia-smi

step "Run day1 full pipeline"
NUM_GPUS="${NUM_GPUS}" \
USE_TORCHRUN="${USE_TORCHRUN}" \
BF16="${BF16}" \
FP16="${FP16}" \
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
JUDGE_MODEL="${JUDGE_MODEL}" \
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES}" \
ALLOW_LAYER_B_BLOCKER="${ALLOW_LAYER_B_BLOCKER}" \
HF_ENDPOINT="${HF_ENDPOINT}" \
bash day1_run.sh

step "Extra audits and figure refresh"
make next-stage
if ! make dpo-ablation; then
  echo "[GPU-ONCE][WARN] dpo-ablation failed; continue with existing artifacts."
fi
"${PYTHON_BIN}" scripts/eval/build_thesis_assets.py || true
"${PYTHON_BIN}" scripts/eval/build_thesis_figures.py
"${PYTHON_BIN}" scripts/audit/build_proposal_compliance_report.py
make gpu-closure

step "Build portable thesis bundle"
bundle_args=(
  --root .
  --out-dir exports
  --tag "gpu_once_${TS}"
  --archive
)
if [[ "${INCLUDE_LOGS_IN_BUNDLE}" == "1" ]]; then
  bundle_args+=(--include-logs)
fi
if [[ "${INCLUDE_CLEAN_DATA_IN_BUNDLE}" == "1" ]]; then
  bundle_args+=(--include-clean-data)
fi
"${PYTHON_BIN}" scripts/deploy/package_thesis_bundle.py "${bundle_args[@]}"

step "Final key paths"
echo "run_log=${RUN_LOG}"
echo "thesis_summary=reports/thesis_assets/thesis_ready_summary.md"
echo "figure_manifest=reports/thesis_assets/figures/figure_manifest.json"
echo "bundle_dir=exports/thesis_bundle_gpu_once_${TS}"
echo "bundle_archive=exports/thesis_bundle_gpu_once_${TS}.tar.gz"
echo "sync_hint: rsync -avz --progress <remote>:${ROOT_DIR}/exports/thesis_bundle_gpu_once_${TS}.tar.gz ./"

if [[ "${AUTO_SHUTDOWN}" == "1" ]]; then
  step "AUTO_SHUTDOWN=1 -> poweroff in 15 seconds"
  sleep 15
  if command -v poweroff >/dev/null 2>&1; then
    poweroff
  else
    shutdown -h now
  fi
fi

step "Done"
