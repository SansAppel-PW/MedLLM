#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

BENCHMARK="${BENCHMARK:-data/benchmark/real_medqa_benchmark.jsonl}"
KB_OUT="${KB_OUT:-data/kg/real_medqa_reference_kb.jsonl}"
KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}"
EVAL_SPLITS="${EVAL_SPLITS:-validation,test}"
DET_MAX="${DET_MAX:-0}"
EVAL_MAX="${EVAL_MAX:-0}"
SOTA_MAX="${SOTA_MAX:-0}"
LOG_EVERY="${LOG_EVERY:-300}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-false}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-120}"
JUDGE_CACHE="${JUDGE_CACHE:-reports/eval/judge_cache.jsonl}"
RUN_BALANCED_DETECTION_AUDIT="${RUN_BALANCED_DETECTION_AUDIT:-true}"

eval_cmd=(
  python3 eval/run_eval.py
  --benchmark "${BENCHMARK}"
  --kg "${KB_OUT}"
  --default-report reports/eval_default.md
  --ablation-kg reports/ablation_kg.md
  --ablation-detection reports/ablation_detection.md
  --ablation-alignment reports/ablation_alignment.md
  --include-splits "${EVAL_SPLITS}"
  --max-samples "${EVAL_MAX}"
  --log-every "${LOG_EVERY}"
  --judge-model "${JUDGE_MODEL}"
  --judge-max-samples "${JUDGE_MAX_SAMPLES}"
  --judge-cache "${JUDGE_CACHE}"
)
if [[ "${ENABLE_LLM_JUDGE}" == "true" ]]; then
  eval_cmd+=(--enable-llm-judge)
fi

python3 scripts/data/build_benchmark_reference_kb.py \
  --benchmark "${BENCHMARK}" \
  --include-splits "${KB_SOURCE_SPLITS}" \
  --output "${KB_OUT}" \
  --report reports/benchmark_reference_kb_report.md

python3 -m src.detect.evaluate_detection \
  --benchmark "${BENCHMARK}" \
  --kg "${KB_OUT}" \
  --pred-output reports/detection_predictions.jsonl \
  --report reports/detection_eval.md \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${DET_MAX}"

python3 scripts/audit/check_benchmark_artifacts.py \
  --benchmark "${BENCHMARK}" \
  --include-splits "${EVAL_SPLITS}" \
  --report reports/thesis_support/benchmark_artifact_report.md \
  --json reports/thesis_support/benchmark_artifact_report.json

if [[ "${RUN_BALANCED_DETECTION_AUDIT}" == "true" ]]; then
  BENCHMARK_SRC="${BENCHMARK}" \
  KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS}" \
  EVAL_SPLITS="${EVAL_SPLITS}" \
  DET_MAX="${DET_MAX}" \
  bash scripts/eval/run_detection_robustness.sh
fi

"${eval_cmd[@]}"

python3 scripts/eval/run_sota_compare.py \
  --benchmark "${BENCHMARK}" \
  --kg "${KB_OUT}" \
  --report reports/sota_compare.md \
  --csv reports/thesis_assets/tables/sota_compare_metrics.csv \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${SOTA_MAX}" \
  --log-every "${LOG_EVERY}"

python3 scripts/eval/generate_error_analysis.py \
  --predictions reports/detection_predictions.jsonl \
  --output reports/error_analysis.md \
  --cases-out reports/thesis_assets/cases/error_cases_top30.jsonl \
  --top-n 30

python3 scripts/eval/build_thesis_assets.py \
  --out-dir reports/thesis_assets \
  --dataset-summary reports/real_dataset_summary.json \
  --predictions reports/detection_predictions.jsonl \
  --sota-csv reports/thesis_assets/tables/sota_compare_metrics.csv

python3 scripts/eval/build_training_figures.py \
  --out-dir reports/thesis_assets/figures \
  --summary-csv reports/thesis_assets/tables/training_loss_summary.csv

python3 scripts/eval/generate_thesis_draft_material.py \
  --dataset-summary reports/real_dataset_summary.json \
  --sft reports/training/layer_b_qwen25_7b_sft_metrics.json \
  --dpo reports/training/dpo_metrics.json \
  --simpo reports/training/simpo_metrics.json \
  --kto reports/training/kto_metrics.json \
  --eval-default reports/eval_default.md \
  --sota-csv reports/thesis_assets/tables/sota_compare_metrics.csv \
  --error-analysis reports/error_analysis.md \
  --resource reports/training/resource_preflight.json \
  --skip-report reports/training/resource_skip_report.md \
  --artifact-report reports/thesis_support/benchmark_artifact_report.json \
  --output-md reports/thesis_support/thesis_draft_material.md \
  --output-json reports/thesis_support/experiment_record.json

python3 scripts/audit/check_thesis_readiness.py \
  --report reports/thesis_support/thesis_readiness.md \
  --json reports/thesis_support/thesis_readiness.json

echo "[thesis-pipeline] done"
