from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def load_module():
    repo = Path(__file__).resolve().parents[1]
    mod_path = repo / "scripts/data/build_real_dataset.py"
    spec = importlib.util.spec_from_file_location("build_real_dataset_module", mod_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_split_rows_small_scale_has_non_zero_train() -> None:
    mod = load_module()
    rows = [{"id": f"r{i}", "query": "q", "answer": "a"} for i in range(600)]
    train, dev, test = mod.split_rows(rows, seed=42)
    assert len(train) > 0
    assert len(dev) > 0
    assert len(test) > 0
    assert len(train) + len(dev) + len(test) == len(rows)


def test_split_rows_tiny_scale_fallback() -> None:
    mod = load_module()
    rows = [{"id": "r0"}, {"id": "r1"}]
    train, dev, test = mod.split_rows(rows, seed=1)
    assert len(train) == 2
    assert len(dev) == 0
    assert len(test) == 0
