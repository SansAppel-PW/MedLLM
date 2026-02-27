#!/usr/bin/env bash
set -euo pipefail

# MedLLM Day1 one-click script (GPU environment)
# Usage:
#   bash day1_run.sh
# Optional env:
#   ENABLE_LLM_JUDGE=1 JUDGE_MODEL=gpt-4o-mini JUDGE_MAX_SAMPLES=200 bash day1_run.sh
#   AUTO_COMMIT_PUSH=1 COMMIT_MSG="milestone: gpu day1 mainline" bash day1_run.sh
#   REQUIRE_GPU=0 SKIP_MAINLINE=1 bash day1_run.sh   # debug only

if [[ "${1:-}" == "--help" ]]; then
  cat <<'USAGE'
Usage: bash day1_run.sh

Default behavior (full Day1 flow):
1) Environment setup (venv + requirements)
2) GPU checks
3) Preflight audits (guard/interface/opening/task/readiness)
4) Dry-run of gpu-mainline
5) Real gpu-mainline execution
6) Closure audits + thesis-ready
7) Strict acceptance gate (gpu-closure fail=0, A10=PASS, Layer-B row exists)

Optional env vars:
- REQUIRE_GPU=1|0              default: 1
- SKIP_INSTALL=1               skip venv/pip install (default: 0)
- SKIP_MAINLINE=1              skip gpu-mainline + strict gate (default: 0)
- ENABLE_LLM_JUDGE=1|0         default: 0
- JUDGE_MODEL=<model>          default: gpt-4o-mini
- JUDGE_MAX_SAMPLES=<int>      default: 200
- PYTHON_BIN=<path>            default: .venv/bin/python if exists else python3
- AUTO_COMMIT_PUSH=1|0         default: 0
- COMMIT_MSG="..."            default: milestone: gpu mainline thesis run <timestamp>
USAGE
  exit 0
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

REQUIRE_GPU="${REQUIRE_GPU:-1}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
SKIP_MAINLINE="${SKIP_MAINLINE:-0}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-0}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-200}"
AUTO_COMMIT_PUSH="${AUTO_COMMIT_PUSH:-0}"

TS="${TS:-$(date +%Y%m%d_%H%M%S)}"
LOG_DIR="logs/session"
mkdir -p "${LOG_DIR}"
RUN_LOG="${LOG_DIR}/day1_run_${TS}.log"
MAINLINE_LOG="${LOG_DIR}/gpu_mainline_${TS}.log"

# Mirror all stdout/stderr to run log.
exec > >(tee -a "${RUN_LOG}") 2>&1

step() {
  echo
  echo "[$(date '+%F %T')] [STEP] $*"
}

fail() {
  echo "[$(date '+%F %T')] [ERROR] $*" >&2
  exit 1
}

step "Validate branch and workspace"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[[ "${BRANCH}" == "codex/worktree-gpt-prompt" ]] || fail "Current branch is '${BRANCH}', expected 'codex/worktree-gpt-prompt'."
git status --short

auto_python_bin() {
  if [[ -x ".venv/bin/python" ]]; then
    echo ".venv/bin/python"
  else
    echo "python3"
  fi
}

PYTHON_BIN="${PYTHON_BIN:-$(auto_python_bin)}"

if [[ "${SKIP_INSTALL}" != "1" ]]; then
  step "Setup Python environment"
  if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  python -m pip install -U pip
  pip install -r requirements.txt
  PYTHON_BIN=".venv/bin/python"
else
  step "Skip install (SKIP_INSTALL=1)"
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  fi
fi

step "Environment check"
"${PYTHON_BIN}" --version
"${PYTHON_BIN}" -m pip --version

if [[ "${REQUIRE_GPU}" == "1" ]]; then
  step "GPU check"
  command -v nvidia-smi >/dev/null 2>&1 || fail "nvidia-smi not found. Use REQUIRE_GPU=0 only for debug dry runs."
  nvidia-smi
  "${PYTHON_BIN}" - <<'PY'
import sys
import torch
print("torch:", torch.__version__)
print("cuda_available:", torch.cuda.is_available())
if not torch.cuda.is_available():
    print("ERROR: CUDA is not available", file=sys.stderr)
    raise SystemExit(2)
print("device0:", torch.cuda.get_device_name(0))
PY
fi

if [[ "${ENABLE_LLM_JUDGE}" == "1" ]]; then
  step "Judge mode enabled; validate .env"
  [[ -f ".env" ]] || fail "ENABLE_LLM_JUDGE=1 requires .env in repo root."
fi

step "Preflight audits"
make check-env
make repo-guard
make interface-audit
make opening-audit
make task-audit
make gpu-readiness

step "GPU mainline dry-run"
PYTHON_BIN="${PYTHON_BIN}" make gpu-mainline-dryrun

if [[ "${SKIP_MAINLINE}" != "1" ]]; then
  step "Run GPU mainline (this can take long)"
  ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
  JUDGE_MODEL="${JUDGE_MODEL}" \
  JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES}" \
  PYTHON_BIN="${PYTHON_BIN}" \
  make gpu-mainline 2>&1 | tee "${MAINLINE_LOG}"

  step "Run closure audits and thesis packaging"
  make gpu-closure
  make opening-audit
  make thesis-ready

  step "Strict acceptance gate"
  "${PYTHON_BIN}" - <<'PY'
import csv
import json
import sys
from pathlib import Path

root = Path('.')

closure = json.loads((root / 'reports/gpu_experiment_closure.json').read_text(encoding='utf-8'))
closure_fail = int(closure.get('summary', {}).get('fail', 999))
if closure_fail != 0:
    print(f"ERROR: gpu_experiment_closure fail={closure_fail}", file=sys.stderr)
    raise SystemExit(3)

opening = json.loads((root / 'reports/opening_alignment_audit.json').read_text(encoding='utf-8'))
a10 = None
for row in opening.get('checks', []):
    if row.get('id') == 'A10':
        a10 = row.get('status')
        break
if a10 != 'PASS':
    print(f"ERROR: A10 status is {a10}, expected PASS", file=sys.stderr)
    raise SystemExit(4)

main_csv = root / 'reports/thesis_assets/tables/main_results_real.csv'
if not main_csv.exists():
    print('ERROR: main_results_real.csv missing', file=sys.stderr)
    raise SystemExit(5)

layer_b_found = False
with main_csv.open(encoding='utf-8', newline='') as f:
    for row in csv.reader(f):
        if any('Qwen2.5-7B Layer-B' in cell for cell in row):
            layer_b_found = True
            break
if not layer_b_found:
    print('ERROR: Layer-B row missing in main_results_real.csv', file=sys.stderr)
    raise SystemExit(6)

print('Strict acceptance gate passed.')
PY
else
  step "Skip mainline and strict gate (SKIP_MAINLINE=1)"
fi

if [[ "${AUTO_COMMIT_PUSH}" == "1" ]]; then
  step "Auto commit + push"
  make repo-guard
  git add -A
  make repo-guard-staged
  COMMIT_MSG="${COMMIT_MSG:-milestone: gpu mainline thesis run ${TS}}"
  if git diff --cached --quiet; then
    echo "No staged changes; skip commit/push."
  else
    git commit -m "${COMMIT_MSG}"
    git push
  fi
fi

step "Completed"
echo "Run log: ${RUN_LOG}"
if [[ "${SKIP_MAINLINE}" != "1" ]]; then
  echo "Mainline log: ${MAINLINE_LOG}"
fi
echo "Key outputs:"
echo "- reports/gpu_experiment_closure.md"
echo "- reports/opening_alignment_audit.md"
echo "- reports/thesis_assets/thesis_ready_summary.md"
