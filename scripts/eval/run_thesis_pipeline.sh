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

python3 eval/run_eval.py \
  --benchmark "${BENCHMARK}" \
  --kg "${KB_OUT}" \
  --default-report reports/eval_default.md \
  --ablation-kg reports/ablation_kg.md \
  --ablation-detection reports/ablation_detection.md \
  --ablation-alignment reports/ablation_alignment.md \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${EVAL_MAX}" \
  --log-every "${LOG_EVERY}"

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

echo "[thesis-pipeline] done"
