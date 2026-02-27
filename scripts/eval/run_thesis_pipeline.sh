#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
BENCHMARK="${BENCHMARK:-data/benchmark/real_medqa_benchmark.jsonl}"
KB_OUT="${KB_OUT:-data/kg/real_medqa_reference_kb.jsonl}"
KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}"
EVAL_SPLITS="${EVAL_SPLITS:-validation,test}"
DET_MAX="${DET_MAX:-0}"
EVAL_MAX="${EVAL_MAX:-0}"
SOTA_MAX="${SOTA_MAX:-0}"
LOG_EVERY="${LOG_EVERY:-300}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-0}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-120}"
JUDGE_RECORDS_DIR="${JUDGE_RECORDS_DIR:-reports/judge/winrate}"
JUDGE_TIMEOUT_SEC="${JUDGE_TIMEOUT_SEC:-60}"

EVAL_JUDGE_ARGS=()
if [[ "${ENABLE_LLM_JUDGE}" == "1" ]]; then
  EVAL_JUDGE_ARGS+=(
    --enable-llm-judge
    --judge-model "${JUDGE_MODEL}"
    --judge-max-samples "${JUDGE_MAX_SAMPLES}"
    --judge-records-dir "${JUDGE_RECORDS_DIR}"
    --judge-timeout-sec "${JUDGE_TIMEOUT_SEC}"
  )
fi

"${PYTHON_BIN}" scripts/data/build_benchmark_reference_kb.py \
  --benchmark "${BENCHMARK}" \
  --include-splits "${KB_SOURCE_SPLITS}" \
  --output "${KB_OUT}" \
  --report reports/benchmark_reference_kb_report.md

"${PYTHON_BIN}" -m src.detect.evaluate_detection \
  --benchmark "${BENCHMARK}" \
  --kg "${KB_OUT}" \
  --pred-output reports/detection_predictions.jsonl \
  --report reports/detection_eval.md \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${DET_MAX}"

"${PYTHON_BIN}" eval/run_eval.py \
  --benchmark "${BENCHMARK}" \
  --kg "${KB_OUT}" \
  --default-report reports/eval_default.md \
  --ablation-kg reports/ablation_kg.md \
  --ablation-detection reports/ablation_detection.md \
  --ablation-alignment reports/ablation_alignment.md \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${EVAL_MAX}" \
  --log-every "${LOG_EVERY}" \
  "${EVAL_JUDGE_ARGS[@]}"

"${PYTHON_BIN}" scripts/eval/run_sota_compare.py \
  --benchmark "${BENCHMARK}" \
  --kg "${KB_OUT}" \
  --report reports/sota_compare.md \
  --csv reports/thesis_assets/tables/sota_compare_metrics.csv \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${SOTA_MAX}" \
  --log-every "${LOG_EVERY}"

"${PYTHON_BIN}" scripts/eval/generate_error_analysis.py \
  --predictions reports/detection_predictions.jsonl \
  --output reports/error_analysis.md \
  --cases-out reports/thesis_assets/cases/error_cases_top30.jsonl \
  --top-n 30

"${PYTHON_BIN}" scripts/eval/build_thesis_assets.py \
  --out-dir reports/thesis_assets \
  --dataset-summary reports/real_dataset_summary.json \
  --predictions reports/detection_predictions.jsonl \
  --sota-csv reports/thesis_assets/tables/sota_compare_metrics.csv

echo "[thesis-pipeline] done"
