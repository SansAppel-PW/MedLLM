#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

BENCHMARK_SRC="${BENCHMARK_SRC:-data/benchmark/real_medqa_benchmark.jsonl}"
BENCHMARK_V2="${BENCHMARK_V2:-data/benchmark/real_medqa_benchmark_v2_balanced.jsonl}"
KB_V2="${KB_V2:-data/kg/real_medqa_reference_kb_v2_balanced.jsonl}"
KB_SOURCE_SPLITS="${KB_SOURCE_SPLITS:-train}"
EVAL_SPLITS="${EVAL_SPLITS:-validation,test}"
DET_MAX="${DET_MAX:-0}"

python3 scripts/data/build_balanced_detection_benchmark.py \
  --input "${BENCHMARK_SRC}" \
  --output "${BENCHMARK_V2}" \
  --report reports/benchmark_v2_balanced_report.md \
  --summary-json reports/benchmark_v2_balanced_summary.json

python3 scripts/data/build_benchmark_reference_kb.py \
  --benchmark "${BENCHMARK_V2}" \
  --include-splits "${KB_SOURCE_SPLITS}" \
  --output "${KB_V2}" \
  --report reports/benchmark_reference_kb_v2_report.md

python3 -m src.detect.evaluate_detection \
  --benchmark "${BENCHMARK_V2}" \
  --kg "${KB_V2}" \
  --pred-output reports/detection_predictions_v2_balanced.jsonl \
  --report reports/detection_eval_v2_balanced.md \
  --include-splits "${EVAL_SPLITS}" \
  --max-samples "${DET_MAX}"

python3 scripts/audit/check_benchmark_artifacts.py \
  --benchmark "${BENCHMARK_V2}" \
  --include-splits "${EVAL_SPLITS}" \
  --report reports/thesis_support/benchmark_artifact_report_v2_balanced.md \
  --json reports/thesis_support/benchmark_artifact_report_v2_balanced.json

echo "[detection-robustness] done"
