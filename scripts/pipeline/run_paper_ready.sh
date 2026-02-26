#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

BUILD_REAL_DATA="${BUILD_REAL_DATA:-auto}"   # auto | true | false
RUN_TRAINING="${RUN_TRAINING:-true}"         # true | false
RUN_EVAL="${RUN_EVAL:-true}"                 # true | false
RUN_E2E="${RUN_E2E:-true}"                   # true | false

ALIGNMENT_MODE="${ALIGNMENT_MODE:-real}"     # proxy | real
MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-7B-Instruct}"
MODEL_TIER="${MODEL_TIER:-auto}"             # auto | small | 7b | 14b
ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING:-true}"
FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING:-false}"

ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-false}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-120}"
JUDGE_CACHE="${JUDGE_CACHE:-reports/eval/judge_cache.jsonl}"

KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}"
EVAL_SPLITS="${EVAL_SPLITS:-validation,test}"
DET_MAX="${DET_MAX:-0}"
EVAL_MAX="${EVAL_MAX:-1200}"
SOTA_MAX="${SOTA_MAX:-1800}"
LOG_EVERY="${LOG_EVERY:-400}"

DATA_SEED="${DATA_SEED:-42}"
DATA_CMT_COUNT="${DATA_CMT_COUNT:-20000}"
DATA_H26_COUNT="${DATA_H26_COUNT:-15000}"
DATA_HENC_COUNT="${DATA_HENC_COUNT:-15000}"
DATA_BENCH_TRAIN="${DATA_BENCH_TRAIN:-2000}"
DATA_BENCH_VAL="${DATA_BENCH_VAL:-600}"
DATA_BENCH_TEST="${DATA_BENCH_TEST:-600}"

STATUS_REPORT="${STATUS_REPORT:-reports/pipeline/paper_ready_status.md}"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

ensure_dir() {
  mkdir -p "$1"
}

run_step() {
  local name="$1"
  shift
  echo "[pipeline] step=${name} start"
  "$@"
  echo "[pipeline] step=${name} done"
}

should_build_data() {
  if [[ "${BUILD_REAL_DATA}" == "true" ]]; then
    return 0
  fi
  if [[ "${BUILD_REAL_DATA}" == "false" ]]; then
    return 1
  fi
  # auto mode: build if key artifacts are missing
  local required=(
    "data/clean/real_sft_train.jsonl"
    "data/clean/real_sft_dev.jsonl"
    "data/benchmark/real_medqa_benchmark.jsonl"
  )
  for f in "${required[@]}"; do
    if [[ ! -f "${f}" ]]; then
      return 0
    fi
  done
  return 1
}

data_status="SKIPPED"
train_status="SKIPPED"
eval_status="SKIPPED"
e2e_status="SKIPPED"

data_note=""
train_note=""
eval_note=""
e2e_note=""
readiness_status="SKIPPED"
readiness_note=""

if should_build_data; then
  run_step "build_real_dataset" \
    python3 scripts/data/build_real_dataset.py \
      --seed "${DATA_SEED}" \
      --cmt-count "${DATA_CMT_COUNT}" \
      --h26-count "${DATA_H26_COUNT}" \
      --henc-count "${DATA_HENC_COUNT}" \
      --bench-train "${DATA_BENCH_TRAIN}" \
      --bench-val "${DATA_BENCH_VAL}" \
      --bench-test "${DATA_BENCH_TEST}"
  data_status="DONE"
  data_note="real dataset rebuilt"
else
  data_status="SKIPPED"
  data_note="existing real dataset reused"
fi

if [[ "${RUN_TRAINING}" == "true" ]]; then
  set +e
  ALIGNMENT_MODE="${ALIGNMENT_MODE}" \
  MODEL_NAME="${MODEL_NAME}" \
  MODEL_TIER="${MODEL_TIER}" \
  ALLOW_SKIP_TRAINING="${ALLOW_SKIP_TRAINING}" \
  FORCE_SKIP_TRAINING="${FORCE_SKIP_TRAINING}" \
  bash scripts/train/run_real_alignment_pipeline.sh
  train_rc=$?
  set -e
  if [[ ${train_rc} -eq 0 ]]; then
    train_status="DONE"
    if [[ -f reports/training/resource_skip_report.md ]]; then
      train_note="training fallback active (see resource_skip_report.md)"
    else
      train_note="real/proxy training pipeline finished"
    fi
  else
    train_status="FAILED"
    train_note="training pipeline exited rc=${train_rc}"
    echo "[pipeline] training failed rc=${train_rc}"
  fi
else
  train_status="SKIPPED"
  train_note="RUN_TRAINING=false"
fi

if [[ "${RUN_EVAL}" == "true" ]]; then
  run_step "thesis_eval" \
    env \
      ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE}" \
      JUDGE_MODEL="${JUDGE_MODEL}" \
      JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES}" \
      JUDGE_CACHE="${JUDGE_CACHE}" \
      KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS}" \
      EVAL_SPLITS="${EVAL_SPLITS}" \
      DET_MAX="${DET_MAX}" \
      EVAL_MAX="${EVAL_MAX}" \
      SOTA_MAX="${SOTA_MAX}" \
      LOG_EVERY="${LOG_EVERY}" \
      bash scripts/eval/run_thesis_pipeline.sh
  eval_status="DONE"
  eval_note="thesis evaluation assets refreshed"
else
  eval_status="SKIPPED"
  eval_note="RUN_EVAL=false"
fi

if [[ "${RUN_E2E}" == "true" ]]; then
  run_step "e2e_acceptance" python3 scripts/deploy/run_e2e_acceptance.py
  e2e_status="DONE"
  e2e_note="demo e2e acceptance refreshed"
else
  e2e_status="SKIPPED"
  e2e_note="RUN_E2E=false"
fi

if [[ -f reports/thesis_support/thesis_readiness.json ]]; then
  read -r fail_count deferred_count < <(
    python3 - <<'PY'
import json
from pathlib import Path
p = Path("reports/thesis_support/thesis_readiness.json")
payload = json.loads(p.read_text(encoding="utf-8"))
summary = payload.get("summary", {})
print(summary.get("FAIL", 0), summary.get("DEFERRED", 0))
PY
  )
  if [[ "${fail_count}" == "0" ]]; then
    readiness_status="DONE"
    readiness_note="FAIL=0, DEFERRED=${deferred_count}"
  else
    readiness_status="WARN"
    readiness_note="FAIL=${fail_count}, DEFERRED=${deferred_count}"
  fi
else
  readiness_status="MISSING"
  readiness_note="thesis_readiness.json not found"
fi

ensure_dir "$(dirname "${STATUS_REPORT}")"
cat > "${STATUS_REPORT}" <<EOF
# Paper-Ready Pipeline Status

- Generated at (UTC): $(timestamp)
- Model target: \`${MODEL_NAME}\`
- Alignment mode: \`${ALIGNMENT_MODE}\`

| Step | Status | Note |
|---|---|---|
| Data Build | ${data_status} | ${data_note} |
| Training | ${train_status} | ${train_note} |
| Evaluation | ${eval_status} | ${eval_note} |
| E2E Acceptance | ${e2e_status} | ${e2e_note} |
| Thesis Readiness | ${readiness_status} | ${readiness_note} |

## Key Outputs
- \`reports/real_dataset_report.md\`
- \`reports/alignment_compare.md\`
- \`reports/eval_default.md\`
- \`reports/sota_compare.md\`
- \`reports/error_analysis.md\`
- \`reports/detection_eval_v2_balanced.md\`
- \`reports/detection_eval_llm_judge.md\` (optional)
- \`reports/thesis_assets/\`
- \`reports/e2e_acceptance.md\`
- \`reports/thesis_support/thesis_draft_material.md\`
- \`reports/thesis_support/benchmark_artifact_report.md\`
- \`reports/thesis_support/benchmark_artifact_report_v2_balanced.md\`
- \`reports/thesis_support/thesis_readiness.md\`
EOF

echo "[pipeline] status=${STATUS_REPORT}"
