#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_ROOT="${ROOT_DIR}/data/raw"
PYTHON_BIN="${PYTHON_BIN:-python3}"
FORCE=0

DEFAULT_DATASETS=("medqa" "cmtmedqa" "huatuo26m")
SELECTED_DATASETS=("medqa" "cmtmedqa" "huatuo26m")

usage() {
  cat <<'EOF'
Usage:
  scripts/data/download_datasets.sh [options]

Options:
  --dataset NAME_OR_REPO   Dataset key (medqa|cmtmedqa|huatuo26m) or HuggingFace repo id (owner/repo).
                           Repeat the option to add multiple datasets.
  --root PATH              Output root directory. Default: data/raw
  --python BIN             Python binary. Default: python3
  --force                  Re-download even if target folder exists
  --list                   Show supported default datasets and exit
  -h, --help               Show this help message

Examples:
  scripts/data/download_datasets.sh
  scripts/data/download_datasets.sh --dataset medqa --dataset cmtmedqa
  scripts/data/download_datasets.sh --dataset some-user/some-medical-dataset --root data/raw
EOF
}

list_defaults() {
  echo "Default datasets:"
  local key repo config
  for key in "${DEFAULT_DATASETS[@]}"; do
    repo="$(dataset_repo "${key}")"
    config="$(dataset_config "${key}")"
    printf "  - %s -> %s" "${key}" "${repo}"
    if [[ -n "${config}" ]]; then
      printf " (config: %s)" "${config}"
    fi
    printf "\n"
  done
}

dataset_repo() {
  case "$1" in
    medqa) echo "fzkuji/MedQA" ;;
    cmtmedqa) echo "Suprit/CMtMedQA" ;;
    huatuo26m) echo "FreedomIntelligence/Huatuo26M-Lite" ;;
    *) return 1 ;;
  esac
}

dataset_config() {
  case "$1" in
    medqa) echo "med_qa_zh_source" ;;
    cmtmedqa) echo "" ;;
    huatuo26m) echo "default" ;;
    *) return 1 ;;
  esac
}

slugify_repo() {
  local repo_id="$1"
  repo_id="${repo_id//\//__}"
  repo_id="${repo_id//:/_}"
  echo "${repo_id}"
}

ensure_python_deps() {
  "${PYTHON_BIN}" - <<'PY'
import importlib.util
import sys

missing = [m for m in ("datasets", "pyarrow") if importlib.util.find_spec(m) is None]
if missing:
    print("Missing python packages:", ", ".join(missing))
    print("Run: make setup  (or python -m pip install -r requirements.txt)")
    sys.exit(1)
PY
}

download_dataset() {
  local dataset_key="$1"
  local repo_id="$2"
  local config_name="$3"

  local target_dir="${OUTPUT_ROOT}/${dataset_key}"

  if [[ -d "${target_dir}" && "${FORCE}" -eq 0 ]]; then
    echo "[skip] ${dataset_key} already exists at ${target_dir} (use --force to overwrite)"
    return 0
  fi

  mkdir -p "${target_dir}"
  echo "[download] ${dataset_key} <- ${repo_id} ${config_name:+(config: ${config_name})}"

  MEDLLM_REPO="${repo_id}" \
  MEDLLM_CONFIG="${config_name}" \
  MEDLLM_OUTDIR="${target_dir}" \
  "${PYTHON_BIN}" - <<'PY'
import json
import os
import pathlib
from datetime import datetime, timezone

from datasets import DatasetDict, load_dataset

repo = os.environ["MEDLLM_REPO"]
config = os.environ.get("MEDLLM_CONFIG", "").strip()
out_dir = pathlib.Path(os.environ["MEDLLM_OUTDIR"])
out_dir.mkdir(parents=True, exist_ok=True)

kwargs = {}
if config:
    kwargs["name"] = config

try:
    ds = load_dataset(repo, **kwargs)
except Exception as exc:
    if config:
        print(f"[warn] load_dataset({repo}, name={config}) failed: {exc}")
        print("[warn] retrying without explicit config ...")
        ds = load_dataset(repo)
        config = ""
    else:
        raise

if isinstance(ds, DatasetDict):
    split_map = ds
else:
    split_map = {"train": ds}

meta = {
    "repo_id": repo,
    "config": config if config else None,
    "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
    "splits": {},
}

for split, split_ds in split_map.items():
    json_path = out_dir / f"{split}.jsonl"
    parquet_path = out_dir / f"{split}.parquet"
    split_ds.to_json(str(json_path), force_ascii=False)
    split_ds.to_parquet(str(parquet_path))
    meta["splits"][split] = {
        "num_rows": split_ds.num_rows,
        "num_columns": len(split_ds.column_names),
        "columns": split_ds.column_names,
        "jsonl": str(json_path),
        "parquet": str(parquet_path),
    }

with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"[ok] saved dataset to {out_dir}")
PY
}

CUSTOM_DATASETS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dataset)
      if [[ $# -lt 2 ]]; then
        echo "Error: --dataset requires a value."
        exit 1
      fi
      CUSTOM_DATASETS+=("$2")
      shift 2
      ;;
    --root)
      if [[ $# -lt 2 ]]; then
        echo "Error: --root requires a value."
        exit 1
      fi
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --python)
      if [[ $# -lt 2 ]]; then
        echo "Error: --python requires a value."
        exit 1
      fi
      PYTHON_BIN="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --list)
      list_defaults
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ${#CUSTOM_DATASETS[@]} -gt 0 ]]; then
  SELECTED_DATASETS=("${CUSTOM_DATASETS[@]}")
fi

mkdir -p "${OUTPUT_ROOT}"
ensure_python_deps

for dataset in "${SELECTED_DATASETS[@]}"; do
  if repo_id="$(dataset_repo "${dataset}" 2>/dev/null)"; then
    config_name="$(dataset_config "${dataset}" 2>/dev/null || true)"
    download_dataset "${dataset}" "${repo_id}" "${config_name}"
    continue
  fi

  if [[ "${dataset}" == */* ]]; then
    dataset_key="$(slugify_repo "${dataset}")"
    download_dataset "${dataset_key}" "${dataset}" ""
    continue
  fi

  echo "[error] Unsupported dataset key: ${dataset}"
  echo "Run --list to see built-in options, or pass a full repo id like owner/repo."
  exit 1
done

echo "[done] dataset download flow finished."
