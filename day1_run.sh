#!/usr/bin/env bash
set -euo pipefail

# Day1 one-command runner for GPU rental environment.
# Usage:
#   bash day1_run.sh
# Optional env:
#   BRANCH=codex/worktree
#   MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
#   MODEL_TIER=7b
#   ENABLE_LLM_JUDGE=false
#   ENABLE_LLM_RISK_JUDGE=true
#   ENABLE_V2_LLM_FALLBACK=true
#   DAY1_DRY_RUN=true   # only validate pipeline, skip real run + strict completion gate

START_EPOCH="$(date +%s)"

log() {
  local now elapsed mins
  now="$(date +%s)"
  elapsed=$((now - START_EPOCH))
  mins=$((elapsed / 60))
  printf '[T+%02dm] %s\n' "${mins}" "$*"
}

die() {
  log "ERROR: $*"
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || die "missing command: ${cmd}"
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

BRANCH="${BRANCH:-codex/worktree}"
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"
MODEL_TIER="${MODEL_TIER:-7b}"
ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING:-false}"
FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING:-false}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-false}"
ENABLE_LLM_RISK_JUDGE="${ENABLE_LLM_RISK_JUDGE:-true}"
ENABLE_V2_LLM_FALLBACK="${ENABLE_V2_LLM_FALLBACK:-true}"
DAY1_DRY_RUN="${DAY1_DRY_RUN:-false}"

RUN_LOG="${RUN_LOG:-reports/migration/day1_gpu_run.log}"
SUMMARY_MD="${SUMMARY_MD:-reports/migration/day1_run_summary.md}"

log "start day1 runner in ${ROOT_DIR}"

require_cmd git
require_cmd make
require_cmd python3
require_cmd nvidia-smi

log "sync repository branch=${BRANCH}"
git fetch --all --prune
if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git checkout "${BRANCH}"
elif git show-ref --verify --quiet "refs/remotes/origin/${BRANCH}"; then
  git checkout -b "${BRANCH}" "origin/${BRANCH}"
else
  die "branch not found locally or remotely: ${BRANCH}"
fi
git pull --ff-only origin "${BRANCH}"

log "current commit: $(git rev-parse --short HEAD)"

if [[ ! -f .env ]]; then
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    log "create .env from current environment"
    cat > .env <<EOF
OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://api.gptsapi.net/v1}
OPENAI_API_KEY=${OPENAI_API_KEY}
EOF
  else
    die ".env missing and OPENAI_API_KEY not set"
  fi
fi
chmod 600 .env || true

log "gpu probe (nvidia-smi)"
nvidia-smi

log "bootstrap environment"
make gpu-bootstrap

log "torch/cuda quick check"
python3 - <<'PY'
import json
import sys
try:
    import torch
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"torch import failed: {exc}")
if not torch.cuda.is_available():
    raise SystemExit("CUDA not available")
mem = 0.0
for i in range(torch.cuda.device_count()):
    mem += float(torch.cuda.get_device_properties(i).total_memory) / (1024**3)
print(json.dumps({
    "torch": torch.__version__,
    "cuda_device_count": torch.cuda.device_count(),
    "cuda_total_mem_gb": round(mem, 2),
}, ensure_ascii=False))
PY

log "handoff readiness check"
make gpu-check

log "dry-run check of gpu runner"
DRY_RUN=true bash scripts/migration/run_gpu_thesis_experiment.sh

mkdir -p "$(dirname "${RUN_LOG}")"

if [[ "${DAY1_DRY_RUN}" == "true" ]]; then
  log "DAY1_DRY_RUN=true -> skip real run"
else
  log "start real gpu run (log: ${RUN_LOG})"
  set +e
  MODEL_NAME="${MODEL_NAME}" \
  MODEL_TIER="${MODEL_TIER}" \
  ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING}" \
  FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING}" \
  ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
  ENABLE_LLM_RISK_JUDGE="${ENABLE_LLM_RISK_JUDGE}" \
  ENABLE_V2_LLM_FALLBACK="${ENABLE_V2_LLM_FALLBACK}" \
  make gpu-run 2>&1 | tee "${RUN_LOG}"
  run_rc=${PIPESTATUS[0]}
  set -e
  if [[ ${run_rc} -ne 0 ]]; then
    die "gpu-run failed, see ${RUN_LOG}"
  fi
fi

log "refresh thesis readiness"
python3 scripts/audit/check_thesis_readiness.py \
  --report reports/thesis_support/thesis_readiness.md \
  --json reports/thesis_support/thesis_readiness.json

strict_pass="SKIPPED"
if [[ "${DAY1_DRY_RUN}" != "true" ]]; then
  log "strict completion gate"
  if make gpu-complete-check; then
    strict_pass="true"
  else
    strict_pass="false"
  fi
fi

log "write summary: ${SUMMARY_MD}"
python3 - <<PY
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

summary_path = Path("${SUMMARY_MD}")
summary_path.parent.mkdir(parents=True, exist_ok=True)

thesis = {}
thesis_path = Path("reports/thesis_support/thesis_readiness.json")
if thesis_path.exists():
    thesis = json.loads(thesis_path.read_text(encoding="utf-8"))

completion = {}
completion_path = Path("reports/migration/gpu_completion_check.json")
if completion_path.exists():
    completion = json.loads(completion_path.read_text(encoding="utf-8"))

summary = thesis.get("summary", {})
lines = [
    "# Day1 GPU Run Summary",
    "",
    f"- Time (UTC): {datetime.now(timezone.utc).isoformat()}",
    f"- Branch: ${BRANCH}",
    f"- Commit: {subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()}",
    f"- Day1 dry-run: ${DAY1_DRY_RUN}",
    f"- strict_pass: ${strict_pass}",
    "",
    "## Thesis Readiness",
    f"- PASS: {summary.get('PASS', 'N/A')}",
    f"- DEFERRED: {summary.get('DEFERRED', 'N/A')}",
    f"- FAIL: {summary.get('FAIL', 'N/A')}",
    f"- ready_for_writing: {thesis.get('ready_for_writing', 'N/A')}",
    f"- ready_with_deferred: {thesis.get('ready_with_deferred', 'N/A')}",
    "",
    "## Completion Gate",
    f"- strict_pass_json: {completion.get('strict_pass', 'N/A')}",
    "",
    "## References",
    "- reports/migration/day1_gpu_run.log",
    "- reports/migration/gpu_run_status.md",
    "- reports/migration/gpu_completion_check.md",
    "- reports/thesis_support/thesis_readiness.md",
]
summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(str(summary_path))
PY

if [[ "${DAY1_DRY_RUN}" != "true" && "${strict_pass}" != "true" ]]; then
  die "day1 finished but strict completion not passed"
fi

log "done"
