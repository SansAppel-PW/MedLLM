#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
TEST_FILE="${TEST_FILE:-data/clean/real_sft_test.jsonl}"
SUMMARY_FILE="${SUMMARY_FILE:-reports/real_dataset_summary.json}"

MIN_REAL_TRAIN="${MIN_REAL_TRAIN:-200}"
MIN_REAL_DEV="${MIN_REAL_DEV:-20}"
MIN_REAL_TEST="${MIN_REAL_TEST:-20}"

FORCE_REBUILD_REAL_DATASET="${FORCE_REBUILD_REAL_DATASET:-0}"

CMT_COUNT="${CMT_COUNT:-120}"
H26_COUNT="${H26_COUNT:-120}"
HENC_COUNT="${HENC_COUNT:-120}"
BENCH_TRAIN="${BENCH_TRAIN:-60}"
BENCH_VAL="${BENCH_VAL:-20}"
BENCH_TEST="${BENCH_TEST:-20}"
REQUEST_INTERVAL="${REQUEST_INTERVAL:-0.1}"

line_count() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    wc -l < "${path}" | tr -d '[:space:]'
  else
    echo "0"
  fi
}

train_count="$(line_count "${TRAIN_FILE}")"
dev_count="$(line_count "${DEV_FILE}")"
test_count="$(line_count "${TEST_FILE}")"

need_build=0
if [[ "${FORCE_REBUILD_REAL_DATASET}" == "1" ]]; then
  need_build=1
fi
if [[ ! -f "${SUMMARY_FILE}" ]]; then
  need_build=1
fi
if (( train_count < MIN_REAL_TRAIN || dev_count < MIN_REAL_DEV || test_count < MIN_REAL_TEST )); then
  need_build=1
fi

if (( need_build == 0 )); then
  echo "[ensure-real-dataset] reuse existing real dataset: train=${train_count} dev=${dev_count} test=${test_count}"
  exit 0
fi

echo "[ensure-real-dataset] rebuild required: train=${train_count} dev=${dev_count} test=${test_count}"
"${PYTHON_BIN}" scripts/data/build_real_dataset.py \
  --seed 42 \
  --cmt-count "${CMT_COUNT}" \
  --h26-count "${H26_COUNT}" \
  --henc-count "${HENC_COUNT}" \
  --bench-train "${BENCH_TRAIN}" \
  --bench-val "${BENCH_VAL}" \
  --bench-test "${BENCH_TEST}" \
  --request-interval "${REQUEST_INTERVAL}"

train_count="$(line_count "${TRAIN_FILE}")"
dev_count="$(line_count "${DEV_FILE}")"
test_count="$(line_count "${TEST_FILE}")"
echo "[ensure-real-dataset] ready: train=${train_count} dev=${dev_count} test=${test_count}"
