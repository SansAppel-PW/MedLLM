#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

BENCHMARK="${BENCHMARK:-data/benchmark/med_hallu_benchmark.jsonl}"
KG="${KG:-data/kg/cmekg_demo.jsonl}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
LOG_EVERY="${LOG_EVERY:-0}"
INCLUDE_SPLITS="${INCLUDE_SPLITS:-}"
ENABLE_LLM_JUDGE="${ENABLE_LLM_JUDGE:-false}"
JUDGE_MODEL="${JUDGE_MODEL:-gpt-4o-mini}"
JUDGE_MAX_SAMPLES="${JUDGE_MAX_SAMPLES:-120}"
JUDGE_CACHE="${JUDGE_CACHE:-reports/eval/judge_cache.jsonl}"

cmd=(
  python3 eval/run_eval.py
  --benchmark "${BENCHMARK}"
  --kg "${KG}"
  --default-report reports/eval_default.md
  --ablation-kg reports/ablation_kg.md
  --ablation-detection reports/ablation_detection.md
  --ablation-alignment reports/ablation_alignment.md
  --include-splits "${INCLUDE_SPLITS}"
  --max-samples "${MAX_SAMPLES}"
  --log-every "${LOG_EVERY}"
  --judge-model "${JUDGE_MODEL}"
  --judge-max-samples "${JUDGE_MAX_SAMPLES}"
  --judge-cache "${JUDGE_CACHE}"
)
if [[ "${ENABLE_LLM_JUDGE}" == "true" ]]; then
  cmd+=(--enable-llm-judge)
fi
"${cmd[@]}"

echo "[run-eval] done"
