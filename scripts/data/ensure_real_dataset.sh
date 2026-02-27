#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
TRAIN_FILE="${TRAIN_FILE:-data/clean/real_sft_train.jsonl}"
DEV_FILE="${DEV_FILE:-data/clean/real_sft_dev.jsonl}"
TEST_FILE="${TEST_FILE:-data/clean/real_sft_test.jsonl}"
SUMMARY_FILE="${SUMMARY_FILE:-reports/real_dataset_summary.json}"
CM3KG_DIR="${CM3KG_DIR:-CM3KG}"
PREFER_CM3KG="${PREFER_CM3KG:-1}"
CM3KG_MAX_SFT_ROWS="${CM3KG_MAX_SFT_ROWS:-60000}"
CM3KG_MAX_BENCHMARK_PAIRS="${CM3KG_MAX_BENCHMARK_PAIRS:-4000}"
CM3KG_MAX_KB_ROWS="${CM3KG_MAX_KB_ROWS:-180000}"

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

if [[ "${PREFER_CM3KG}" == "1" && -d "${CM3KG_DIR}" ]]; then
  # If CM3KG is present, raise bar to enforce real-scale datasets by default.
  if [[ -z "${MIN_REAL_TRAIN_OVERRIDE:-}" ]]; then
    MIN_REAL_TRAIN=5000
    MIN_REAL_DEV=500
    MIN_REAL_TEST=500
  fi
fi

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

if [[ "${PREFER_CM3KG}" == "1" && -d "${CM3KG_DIR}" ]]; then
  echo "[ensure-real-dataset] CM3KG detected, build real assets from local CM3KG."
  set +e
  "${PYTHON_BIN}" scripts/data/build_cm3kg_real_assets.py \
    --cm3kg-dir "${CM3KG_DIR}" \
    --seed 42 \
    --max-sft-rows "${CM3KG_MAX_SFT_ROWS}" \
    --max-benchmark-pairs "${CM3KG_MAX_BENCHMARK_PAIRS}" \
    --max-kb-rows "${CM3KG_MAX_KB_ROWS}"
  cm3kg_rc=$?
  set -e

  if [[ "${cm3kg_rc}" -eq 0 ]]; then
    train_count="$(line_count "${TRAIN_FILE}")"
    dev_count="$(line_count "${DEV_FILE}")"
    test_count="$(line_count "${TEST_FILE}")"
    if (( train_count >= MIN_REAL_TRAIN && dev_count >= MIN_REAL_DEV && test_count >= MIN_REAL_TEST )); then
      echo "[ensure-real-dataset] CM3KG build ready: train=${train_count} dev=${dev_count} test=${test_count}"
      exit 0
    fi
    echo "[ensure-real-dataset] warn: CM3KG build size below threshold, fallback to alternate builder."
  else
    echo "[ensure-real-dataset] warn: CM3KG build failed (rc=${cm3kg_rc}), fallback to alternate builder."
  fi
fi

echo "[ensure-real-dataset] rebuild required: train=${train_count} dev=${dev_count} test=${test_count}"
set +e
"${PYTHON_BIN}" scripts/data/build_real_dataset.py \
  --seed 42 \
  --cmt-count "${CMT_COUNT}" \
  --h26-count "${H26_COUNT}" \
  --henc-count "${HENC_COUNT}" \
  --bench-train "${BENCH_TRAIN}" \
  --bench-val "${BENCH_VAL}" \
  --bench-test "${BENCH_TEST}" \
  --request-interval "${REQUEST_INTERVAL}"
build_rc=$?
set -e

if [[ "${build_rc}" -ne 0 ]]; then
  echo "[ensure-real-dataset] warn: real dataset build failed (rc=${build_rc}), fallback to local governance pipeline."
  "${PYTHON_BIN}" scripts/data/bootstrap_minimal_assets.py
  "${PYTHON_BIN}" scripts/data/run_data_governance_pipeline.py --seed 42

  if [[ -f "data/clean/sft_train.jsonl" ]]; then
    cp "data/clean/sft_train.jsonl" "${TRAIN_FILE}"
  fi
  if [[ -f "data/clean/sft_dev.jsonl" ]]; then
    cp "data/clean/sft_dev.jsonl" "${DEV_FILE}"
    cp "data/clean/sft_dev.jsonl" "${TEST_FILE}"
  fi

  if [[ ! -f "data/benchmark/real_medqa_benchmark.jsonl" ]]; then
    "${PYTHON_BIN}" scripts/data/bootstrap_minimal_assets.py --force
  fi

  "${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

root = Path(".").resolve()
train = root / "data/clean/real_sft_train.jsonl"
dev = root / "data/clean/real_sft_dev.jsonl"
test = root / "data/clean/real_sft_test.jsonl"
bench = root / "data/benchmark/real_medqa_benchmark.jsonl"

def count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())

payload = {
    "sources": [
        {
            "name": "fallback_local_governance_pipeline",
            "dataset": "local_bootstrap_minimal_assets",
            "config": "default",
            "split": "train/dev/test",
            "num_rows_total": count(train) + count(dev) + count(test),
            "start_offset": 0,
            "target_count": count(train) + count(dev) + count(test),
            "fetched_count": count(train) + count(dev) + count(test),
            "license": "synthetic-demo",
            "fallback": True,
        }
    ],
    "merged_before_dedup": count(train) + count(dev) + count(test),
    "merged_after_dedup": count(train) + count(dev) + count(test),
    "train_count": count(train),
    "dev_count": count(dev),
    "test_count": count(test),
    "benchmark_count": count(bench),
    "seed": 42,
    "fallback_mode": True,
}
out = root / "reports/real_dataset_summary.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
fi

train_count="$(line_count "${TRAIN_FILE}")"
dev_count="$(line_count "${DEV_FILE}")"
test_count="$(line_count "${TEST_FILE}")"

if (( train_count == 0 || dev_count == 0 || test_count == 0 )); then
  echo "[ensure-real-dataset] error: dataset fallback still invalid train=${train_count} dev=${dev_count} test=${test_count}" >&2
  exit 2
fi

echo "[ensure-real-dataset] ready: train=${train_count} dev=${dev_count} test=${test_count}"
