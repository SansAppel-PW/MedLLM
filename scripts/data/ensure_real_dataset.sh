#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
TEST_FILE="${TEST_FILE:-data/clean/real_sft_test.jsonl}"
BENCHMARK_FILE="${BENCHMARK_FILE:-data/benchmark/real_medqa_benchmark.jsonl}"
SUMMARY_FILE="${SUMMARY_FILE:-reports/real_dataset_summary.json}"

CM3KG_DIR="${CM3KG_DIR:-CM3KG}"
PREFER_CM3KG="${PREFER_CM3KG:-1}"

CM3KG_TRAIN="${CM3KG_TRAIN:-data/clean/cm3kg_sft_train.jsonl}"
CM3KG_DEV="${CM3KG_DEV:-data/clean/cm3kg_sft_dev.jsonl}"
CM3KG_TEST="${CM3KG_TEST:-data/clean/cm3kg_sft_test.jsonl}"
CM3KG_BENCH="${CM3KG_BENCH:-data/benchmark/cm3kg_benchmark.jsonl}"
CM3KG_SUMMARY="${CM3KG_SUMMARY:-reports/cm3kg_dataset_summary.json}"
CM3KG_REPORT="${CM3KG_REPORT:-reports/cm3kg_dataset_report.md}"

HF_BENCHMARK_FILE="${HF_BENCHMARK_FILE:-data/benchmark/real_medqa_benchmark_from_hf.jsonl}"
HF_SUMMARY_FILE="${HF_SUMMARY_FILE:-reports/hf_real_dataset_summary.json}"
HF_REPORT_FILE="${HF_REPORT_FILE:-reports/hf_real_dataset_report.md}"

CM3KG_MAX_SFT_ROWS="${CM3KG_MAX_SFT_ROWS:-60000}"
CM3KG_MAX_BENCHMARK_PAIRS="${CM3KG_MAX_BENCHMARK_PAIRS:-4000}"
CM3KG_MAX_KB_ROWS="${CM3KG_MAX_KB_ROWS:-180000}"

RAW_CMT_TARGET="${RAW_CMT_TARGET:-20000}"
RAW_H26_TARGET="${RAW_H26_TARGET:-15000}"
RAW_HENC_TARGET="${RAW_HENC_TARGET:-15000}"
RAW_BENCH_TRAIN="${RAW_BENCH_TRAIN:-2000}"
RAW_BENCH_VAL="${RAW_BENCH_VAL:-600}"
RAW_BENCH_TEST="${RAW_BENCH_TEST:-600}"
RAW_REQUEST_INTERVAL="${RAW_REQUEST_INTERVAL:-0.2}"

MIN_REAL_TRAIN="${MIN_REAL_TRAIN:-200}"
MIN_REAL_DEV="${MIN_REAL_DEV:-20}"
MIN_REAL_TEST="${MIN_REAL_TEST:-20}"

MIN_CMT_COUNT="${MIN_CMT_COUNT:-5000}"
MIN_H26_COUNT="${MIN_H26_COUNT:-5000}"
MIN_HENC_COUNT="${MIN_HENC_COUNT:-5000}"
MIN_MERGED_COUNT="${MIN_MERGED_COUNT:-15000}"
MIN_MEDQA_BENCH_COUNT="${MIN_MEDQA_BENCH_COUNT:-2000}"

FORCE_REBUILD_REAL_DATASET="${FORCE_REBUILD_REAL_DATASET:-0}"

line_count() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    wc -l < "${path}" | tr -d '[:space:]'
  else
    echo "0"
  fi
}

has_unified_summary() {
  if [[ ! -f "${SUMMARY_FILE}" ]]; then
    return 1
  fi
  "${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
path = Path("reports/real_dataset_summary.json")
try:
    obj = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if "source_requirements" in obj and "final_sft" in obj:
    raise SystemExit(0)
raise SystemExit(1)
PY
}

train_count="$(line_count "${TRAIN_FILE}")"
dev_count="$(line_count "${DEV_FILE}")"
test_count="$(line_count "${TEST_FILE}")"

if [[ "${PREFER_CM3KG}" == "1" && -d "${CM3KG_DIR}" ]]; then
  # Proposal-aligned floor when CM3KG exists locally.
  if [[ -z "${MIN_REAL_TRAIN_OVERRIDE:-}" ]]; then
    MIN_REAL_TRAIN=5000
    MIN_REAL_DEV=500
    MIN_REAL_TEST=500
  fi
fi

cmt_count="$(line_count data/raw/real_sources/cmtmedqa.jsonl)"
h26_count="$(line_count data/raw/real_sources/huatuo26m_lite.jsonl)"
henc_count="$(line_count data/raw/real_sources/huatuo_encyclopedia.jsonl)"
merged_count="$(line_count data/raw/real_sources/merged_real_qa.jsonl)"
hf_bench_count="$(line_count "${HF_BENCHMARK_FILE}")"

raw_ready=0
if (( cmt_count >= MIN_CMT_COUNT && h26_count >= MIN_H26_COUNT && henc_count >= MIN_HENC_COUNT && merged_count >= MIN_MERGED_COUNT && hf_bench_count >= MIN_MEDQA_BENCH_COUNT )); then
  raw_ready=1
fi

need_build=0
if [[ "${FORCE_REBUILD_REAL_DATASET}" == "1" ]]; then
  need_build=1
fi
if (( train_count < MIN_REAL_TRAIN || dev_count < MIN_REAL_DEV || test_count < MIN_REAL_TEST )); then
  need_build=1
fi
if [[ ! -f "${SUMMARY_FILE}" ]]; then
  need_build=1
fi
if ! has_unified_summary; then
  need_build=1
fi
if (( raw_ready == 0 )); then
  need_build=1
fi

if (( need_build == 0 )); then
  echo "[ensure-real-dataset] reuse unified real dataset: train=${train_count} dev=${dev_count} test=${test_count}"
  exit 0
fi

echo "[ensure-real-dataset] step1: ensure external real QA sources (CMtMedQA/Huatuo/MedQA benchmark)."
"${PYTHON_BIN}" scripts/data/build_real_dataset.py \
  --seed 42 \
  --cmt-count "${RAW_CMT_TARGET}" \
  --h26-count "${RAW_H26_TARGET}" \
  --henc-count "${RAW_HENC_TARGET}" \
  --bench-train "${RAW_BENCH_TRAIN}" \
  --bench-val "${RAW_BENCH_VAL}" \
  --bench-test "${RAW_BENCH_TEST}" \
  --request-interval "${RAW_REQUEST_INTERVAL}" \
  --benchmark-out "${HF_BENCHMARK_FILE}" \
  --summary-out "${HF_SUMMARY_FILE}" \
  --report-out "${HF_REPORT_FILE}"

echo "[ensure-real-dataset] step2: ensure CM3KG assets (when available)."
if [[ "${PREFER_CM3KG}" == "1" && -d "${CM3KG_DIR}" ]]; then
  "${PYTHON_BIN}" scripts/data/build_cm3kg_real_assets.py \
    --cm3kg-dir "${CM3KG_DIR}" \
    --seed 42 \
    --max-sft-rows "${CM3KG_MAX_SFT_ROWS}" \
    --max-benchmark-pairs "${CM3KG_MAX_BENCHMARK_PAIRS}" \
    --max-kb-rows "${CM3KG_MAX_KB_ROWS}" \
    --train-out "${CM3KG_TRAIN}" \
    --dev-out "${CM3KG_DEV}" \
    --test-out "${CM3KG_TEST}" \
    --benchmark-out "${CM3KG_BENCH}" \
    --kb-out "data/kg/cm3kg_core_kb.jsonl" \
    --summary-out "${CM3KG_SUMMARY}" \
    --report-out "${CM3KG_REPORT}"
else
  echo "[ensure-real-dataset] warning: CM3KG directory missing, skip CM3KG asset build."
fi

echo "[ensure-real-dataset] step3: build unified real assets."
"${PYTHON_BIN}" scripts/data/build_unified_real_assets.py \
  --seed 42 \
  --cm3kg-train "${CM3KG_TRAIN}" \
  --cm3kg-dev "${CM3KG_DEV}" \
  --cm3kg-test "${CM3KG_TEST}" \
  --raw-merged "data/raw/real_sources/merged_real_qa.jsonl" \
  --medqa-benchmark "${HF_BENCHMARK_FILE}" \
  --cm3kg-benchmark "${CM3KG_BENCH}" \
  --out-train "${TRAIN_FILE}" \
  --out-dev "${DEV_FILE}" \
  --out-test "${TEST_FILE}" \
  --out-benchmark "${BENCHMARK_FILE}" \
  --summary-out "${SUMMARY_FILE}" \
  --report-out "reports/real_dataset_report.md"

train_count="$(line_count "${TRAIN_FILE}")"
dev_count="$(line_count "${DEV_FILE}")"
test_count="$(line_count "${TEST_FILE}")"
bench_count="$(line_count "${BENCHMARK_FILE}")"

if (( train_count == 0 || dev_count == 0 || test_count == 0 || bench_count == 0 )); then
  echo "[ensure-real-dataset] error: unified dataset invalid train=${train_count} dev=${dev_count} test=${test_count} bench=${bench_count}" >&2
  exit 2
fi

echo "[ensure-real-dataset] ready: train=${train_count} dev=${dev_count} test=${test_count} benchmark=${bench_count}"
