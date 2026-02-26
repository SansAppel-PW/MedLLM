PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip

.PHONY: setup install check-env repo-guard repo-guard-staged run-config clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install:
	$(PYTHON) -m pip install -r requirements.txt

check-env:
	$(PYTHON) --version
	$(PYTHON) -m pip --version

repo-guard:
	$(PYTHON) scripts/repo_guard.py --mode preadd --max-size-mb 10

repo-guard-staged:
	$(PYTHON) scripts/repo_guard.py --mode staged --max-size-mb 10

run-config:
	@if [ -z "$(CONFIG)" ]; then echo "Usage: make run-config CONFIG=configs/train/sft.yaml"; exit 1; fi
	$(PYTHON) scripts/run_with_config.py --config $(CONFIG) --dry-run

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
