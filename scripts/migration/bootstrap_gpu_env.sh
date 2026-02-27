#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
INSTALL_METHOD="${INSTALL_METHOD:-venv}"     # venv | system
PIP_EXTRA_INDEX_URL="${PIP_EXTRA_INDEX_URL:-}" # e.g. https://download.pytorch.org/whl/cu121

echo "[gpu-bootstrap] root=${ROOT_DIR}"
echo "[gpu-bootstrap] python=${PYTHON_BIN} install_method=${INSTALL_METHOD}"

if [[ "${INSTALL_METHOD}" == "venv" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"
fi

python -m pip install --upgrade pip wheel setuptools
if [[ -n "${PIP_EXTRA_INDEX_URL}" ]]; then
  python -m pip install -r requirements.txt --extra-index-url "${PIP_EXTRA_INDEX_URL}"
else
  python -m pip install -r requirements.txt
fi

python - <<'PY'
import json
import platform

payload = {
    "python": platform.python_version(),
    "platform": platform.platform(),
    "accelerator": "cpu",
    "cuda_device_count": 0,
    "cuda_total_mem_gb": 0.0,
}
try:
    import torch

    if torch.cuda.is_available():
        payload["accelerator"] = "cuda"
        payload["cuda_device_count"] = int(torch.cuda.device_count())
        total = 0.0
        for i in range(torch.cuda.device_count()):
            total += float(torch.cuda.get_device_properties(i).total_memory) / (1024**3)
        payload["cuda_total_mem_gb"] = round(total, 2)
    elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        payload["accelerator"] = "mps"
except Exception as exc:  # noqa: BLE001
    payload["probe_error"] = str(exc)

print("[gpu-bootstrap] probe", json.dumps(payload, ensure_ascii=False))
if payload["accelerator"] != "cuda":
    print("[gpu-bootstrap] warning: CUDA not detected, real 7B/14B training may be skipped or fail.")
PY

echo "[gpu-bootstrap] done"
