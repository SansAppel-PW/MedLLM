#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

python3 eval/run_eval.py \
  --benchmark data/benchmark/med_hallu_benchmark.jsonl \
  --kg data/kg/cmekg_demo.jsonl \
  --default-report reports/eval_default.md \
  --ablation-kg reports/ablation_kg.md \
  --ablation-detection reports/ablation_detection.md \
  --ablation-alignment reports/ablation_alignment.md

echo "[run-eval] done"
