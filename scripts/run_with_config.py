#!/usr/bin/env python3
"""Generic config runner.

Usage:
  python scripts/run_with_config.py --config configs/train/sft.yaml --dry-run
  python scripts/run_with_config.py --config configs/train/sft.yaml
"""

from __future__ import annotations

import argparse
import copy
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - startup guard
    print("Missing dependency: PyYAML", file=sys.stderr)
    print("Run `make setup` or `python -m pip install -r requirements.txt` first.", file=sys.stderr)
    raise SystemExit(1) from exc


def deep_merge(base: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in child.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_inherit_path(config_path: Path, inherits: str) -> Path:
    parent_ref = Path(inherits)
    if parent_ref.is_absolute():
        return parent_ref

    # Try from current config dir upward until we find an existing target.
    candidates = []
    for ancestor in [config_path.parent, *config_path.parents]:
        candidate = (ancestor / parent_ref).resolve()
        if candidate not in candidates:
            candidates.append(candidate)
            if candidate.exists():
                return candidate

    # Fall back to config-relative path for clearer error trace if missing.
    return (config_path.parent / parent_ref).resolve()


def load_yaml_with_inheritance(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        current = yaml.safe_load(f) or {}

    inherits = current.get("inherits")
    if not inherits:
        return current

    parent_path = resolve_inherit_path(config_path, inherits)
    parent_cfg = load_yaml_with_inheritance(parent_path)
    current = {k: v for k, v in current.items() if k != "inherits"}
    return deep_merge(parent_cfg, current)


def apply_overrides(cfg: Dict[str, Any], overrides: list[str]) -> Dict[str, Any]:
    result = copy.deepcopy(cfg)
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"Invalid override '{item}'. Expected key.path=value")
        path, raw_value = item.split("=", 1)
        value: Any = raw_value
        if raw_value.lower() in {"true", "false"}:
            value = raw_value.lower() == "true"
        else:
            try:
                if "." in raw_value:
                    value = float(raw_value)
                else:
                    value = int(raw_value)
            except ValueError:
                value = raw_value

        keys = path.split(".")
        cursor = result
        for key in keys[:-1]:
            if key not in cursor or not isinstance(cursor[key], dict):
                cursor[key] = {}
            cursor = cursor[key]
        cursor[keys[-1]] = value
    return result


def build_command(cfg: Dict[str, Any], config_path: Path) -> list[str]:
    run_cfg = cfg.get("run", {})
    entrypoint = run_cfg.get("entrypoint")
    if not entrypoint:
        raise ValueError("Config missing run.entrypoint")

    runner = run_cfg.get("runner", "auto")
    python_bin = run_cfg.get("python", sys.executable)
    if runner == "python" or (runner == "auto" and entrypoint.endswith(".py")):
        cmd = [python_bin, entrypoint]
    elif runner == "bash" or (runner == "auto" and entrypoint.endswith(".sh")):
        cmd = ["bash", entrypoint]
    else:
        cmd = [entrypoint]

    cmd.extend(["--config", str(config_path)])

    task = run_cfg.get("task")
    if task:
        cmd.extend(["--task", str(task)])

    extra_args = run_cfg.get("args", [])
    if isinstance(extra_args, list):
        cmd.extend([str(x) for x in extra_args])

    kv_args = run_cfg.get("kv_args", {})
    if isinstance(kv_args, dict):
        for key, value in kv_args.items():
            cmd.extend([f"--{key}", str(value)])

    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a job from YAML config.")
    parser.add_argument("--config", required=True, help="Path to yaml config")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Override value with key.path=value",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print command only",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    cfg = load_yaml_with_inheritance(config_path)
    cfg = apply_overrides(cfg, args.override)
    cmd = build_command(cfg, config_path)
    print(" ".join(cmd))

    if args.dry_run:
        return 0

    completed = subprocess.run(cmd, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
