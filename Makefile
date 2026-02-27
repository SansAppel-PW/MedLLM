PYTHON := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)
VENV := .venv
PIP := $(PYTHON) -m pip

.PHONY: setup install check-env repo-guard repo-guard-staged opening-audit task-audit interface-audit gpu-readiness gpu-closure bootstrap-data ensure-real-data small-real small-real-dpo dpo-ablation qwen-layer-b real-alignment gpu-mainline gpu-mainline-dryrun decision-log loop-once thesis-ready run-config clean

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

opening-audit:
	$(PYTHON) scripts/audit/check_opening_alignment.py

task-audit:
	$(PYTHON) scripts/audit/check_task_completion.py

interface-audit:
	$(PYTHON) scripts/audit/check_pipeline_interface_consistency.py

gpu-readiness:
	$(PYTHON) scripts/audit/check_gpu_migration_readiness.py

gpu-closure:
	$(PYTHON) scripts/audit/verify_gpu_experiment_closure.py

bootstrap-data:
	$(PYTHON) scripts/data/bootstrap_minimal_assets.py

ensure-real-data:
	PYTHON_BIN="$(PYTHON)" bash scripts/data/ensure_real_dataset.sh

small-real:
	bash scripts/train/run_small_real_pipeline.sh

small-real-dpo:
	bash scripts/train/run_small_real_dpo_pipeline.sh

dpo-ablation:
	bash scripts/train/run_small_real_dpo_ablation.sh

qwen-layer-b:
	bash scripts/train/run_layer_b_qwen_autofallback.sh

real-alignment:
	PYTHON_BIN="$(PYTHON)" ALIGNMENT_MODE=real SKIP_LAYER_B=1 bash scripts/train/run_real_alignment_pipeline.sh

gpu-mainline:
	PYTHON_BIN="$(PYTHON)" bash scripts/train/run_gpu_thesis_mainline.sh

gpu-mainline-dryrun:
	PYTHON_BIN="$(PYTHON)" DRY_RUN=1 bash scripts/train/run_gpu_thesis_mainline.sh

decision-log:
	$(PYTHON) scripts/audit/update_decision_log.py

loop-once:
	PYTHON_BIN="$(PYTHON)" bash scripts/run_autonomous_iteration.sh

thesis-ready:
	$(PYTHON) scripts/audit/build_thesis_ready_package.py

run-config:
	@if [ -z "$(CONFIG)" ]; then echo "Usage: make run-config CONFIG=configs/train/sft.yaml"; exit 1; fi
	$(PYTHON) scripts/run_with_config.py --config $(CONFIG) --dry-run

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
