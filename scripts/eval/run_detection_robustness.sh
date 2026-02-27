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
ENABLE_V2_LLM_FALLBACK="${ENABLE_V2_LLM_FALLBACK:-false}"
V2_LLM_MODEL="${V2_LLM_MODEL:-gpt-4o-mini}"
V2_LLM_CACHE="${V2_LLM_CACHE:-reports/eval/judge_risk_cache_v2.jsonl}"
V2_LLM_MIN_CONF="${V2_LLM_MIN_CONF:-0.70}"
V2_LLM_MAX_CALLS="${V2_LLM_MAX_CALLS:-0}"

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

if [[ "${ENABLE_V2_LLM_FALLBACK}" == "true" ]]; then
  python3 -m src.detect.evaluate_detection \
    --benchmark "${BENCHMARK_V2}" \
    --kg "${KB_V2}" \
    --pred-output reports/detection_predictions_v2_hybrid_llm.jsonl \
    --report reports/detection_eval_v2_hybrid_llm.md \
    --include-splits "${EVAL_SPLITS}" \
    --max-samples "${DET_MAX}" \
    --enable-llm-fallback \
    --llm-model "${V2_LLM_MODEL}" \
    --llm-cache "${V2_LLM_CACHE}" \
    --llm-min-confidence "${V2_LLM_MIN_CONF}" \
    --llm-max-calls "${V2_LLM_MAX_CALLS}"

  python3 scripts/eval/analyze_llm_fallback_impact.py \
    --predictions reports/detection_predictions_v2_hybrid_llm.jsonl \
    --report reports/detection_eval_v2_hybrid_llm_impact.md \
    --csv reports/thesis_assets/tables/detection_v2_hybrid_llm_impact.csv \
    --json reports/thesis_support/detection_v2_hybrid_llm_impact.json \
    --include-splits "${EVAL_SPLITS}" \
    --max-samples "${DET_MAX}"
fi

echo "[detection-robustness] done"
