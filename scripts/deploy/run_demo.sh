#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
MODE="cli"
if [[ ${1:-} == "--api" ]]; then
  MODE="api"
elif [[ ${1:-} == "--web" ]]; then
  MODE="web"
fi

if [[ "${MODE}" == "api" ]]; then
  echo "[demo] starting API on http://127.0.0.1:8000"
  "${PYTHON_BIN}" -m src.serve.app --serve --host 127.0.0.1 --port 8000
  exit 0
fi

if [[ "${MODE}" == "web" ]]; then
  echo "[demo] static page at http://127.0.0.1:8080/demo/index.html"
  "${PYTHON_BIN}" -m http.server 8080
  exit 0
fi

echo "[demo] running scripted CLI demo"
"${PYTHON_BIN}" demo/run_demo.py
