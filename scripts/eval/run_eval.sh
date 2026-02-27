#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
BENCHMARK="${BENCHMARK:-data/benchmark/med_hallu_benchmark.jsonl}"
KG="${KG:-data/kg/cmekg_demo.jsonl}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
LOG_EVERY="${LOG_EVERY:-0}"
INCLUDE_SPLITS="${INCLUDE_SPLITS:-}"

"${PYTHON_BIN}" eval/run_eval.py \
  --benchmark "${BENCHMARK}" \
  --kg "${KG}" \
  --default-report reports/eval_default.md \
  --ablation-kg reports/ablation_kg.md \
  --ablation-detection reports/ablation_detection.md \
  --ablation-alignment reports/ablation_alignment.md \
  --include-splits "${INCLUDE_SPLITS}" \
  --max-samples "${MAX_SAMPLES}" \
  --log-every "${LOG_EVERY}"

echo "[run-eval] done"
