PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip

.PHONY: setup install check-env run-config paper-ready gpu-manifest gpu-check gpu-bootstrap gpu-run clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install:
	$(PYTHON) -m pip install -r requirements.txt

check-env:
	$(PYTHON) --version
	$(PYTHON) -m pip --version

run-config:
	@if [ -z "$(CONFIG)" ]; then echo "Usage: make run-config CONFIG=configs/train/sft.yaml"; exit 1; fi
	$(PYTHON) scripts/run_with_config.py --config $(CONFIG) --dry-run

paper-ready:
	bash scripts/pipeline/run_paper_ready.sh

gpu-manifest:
	$(PYTHON) scripts/migration/build_gpu_handoff_manifest.py

gpu-check:
	$(PYTHON) scripts/migration/check_handoff_readiness.py

gpu-bootstrap:
	bash scripts/migration/bootstrap_gpu_env.sh

gpu-run:
	bash scripts/migration/run_gpu_thesis_experiment.sh

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
