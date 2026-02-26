#!/usr/bin/env python3
"""Guard script to prevent staging large/sensitive assets."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


BLOCKED_PREFIXES = (
    "data/",
    "datasets/",
    "raw/",
    "processed/",
    "checkpoints/",
    "models/",
    "outputs/",
)

WEIGHT_SUFFIXES = (".bin", ".pt", ".pth", ".ckpt", ".safetensors", ".gguf")
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".7z")
LARGE_DATA_SUFFIXES = (".parquet", ".arrow", ".jsonl")


@dataclass
class Finding:
    rule: str
    path: str
    detail: str


def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def parse_status_path(raw_path: str) -> str:
    if " -> " in raw_path:
        return raw_path.split(" -> ", 1)[1]
    return raw_path


def list_candidate_files(mode: str) -> list[str]:
    files: set[str] = set()
    if mode == "staged":
        out = run_git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
        for line in out.splitlines():
            line = line.strip()
            if line:
                files.add(normalize_path(line))
        return sorted(files)

    status = run_git("status", "--porcelain=1", "--untracked-files=all")
    for line in status.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        raw_path = line[3:].strip()
        path = normalize_path(parse_status_path(raw_path))
        if not path:
            continue
        if "D" in xy:
            continue
        files.add(path)
    return sorted(files)


def staged_blob_size(path: str) -> int | None:
    try:
        out = run_git("cat-file", "-s", f":{path}")
        return int(out)
    except Exception:  # noqa: BLE001
        return None


def file_size(path: str, mode: str) -> int | None:
    if mode == "staged":
        staged = staged_blob_size(path)
        if staged is not None:
            return staged
    p = Path(path)
    if p.exists() and p.is_file():
        return p.stat().st_size
    return None


def in_blocked_prefix(path: str) -> str | None:
    for prefix in BLOCKED_PREFIXES:
        root = prefix.rstrip("/")
        if path == root or path.startswith(prefix):
            return prefix
    return None


def endswith_any(path: str, suffixes: tuple[str, ...]) -> str | None:
    low = path.lower()
    for suffix in suffixes:
        if low.endswith(suffix):
            return suffix
    return None


def evaluate_paths(paths: list[str], mode: str, max_size_mb: float) -> tuple[list[Finding], list[Finding]]:
    violations: list[Finding] = []
    warnings: list[Finding] = []
    max_bytes = int(max_size_mb * 1024 * 1024)

    for path in paths:
        basename = Path(path).name
        size = file_size(path, mode)

        if basename == ".env" or basename.startswith(".env."):
            violations.append(Finding("secret", path, "Staged .env secrets are forbidden"))

        blocked = in_blocked_prefix(path)
        if blocked:
            violations.append(Finding("blocked_path", path, f"Path under blocked prefix `{blocked}`"))

        weight_suffix = endswith_any(path, WEIGHT_SUFFIXES)
        if weight_suffix:
            violations.append(Finding("weights", path, f"Weight file suffix `{weight_suffix}` is forbidden"))

        archive_suffix = endswith_any(path, ARCHIVE_SUFFIXES)
        if archive_suffix:
            violations.append(Finding("archive", path, f"Archive suffix `{archive_suffix}` is forbidden"))

        if size is not None and size > max_bytes:
            violations.append(
                Finding(
                    "large_file",
                    path,
                    f"File size {size / (1024 * 1024):.2f}MB exceeds threshold {max_size_mb:.2f}MB",
                )
            )

        heavy_data = endswith_any(path, LARGE_DATA_SUFFIXES)
        if heavy_data:
            if size is not None and size > max_bytes:
                violations.append(
                    Finding(
                        "large_data",
                        path,
                        f"Data suffix `{heavy_data}` with large size {size / (1024 * 1024):.2f}MB",
                    )
                )
            else:
                warnings.append(
                    Finding(
                        "data_suffix",
                        path,
                        f"Data suffix `{heavy_data}` detected; verify it is lightweight and non-sensitive",
                    )
                )

    return violations, warnings


def print_findings(title: str, findings: list[Finding]) -> None:
    if not findings:
        return
    print(title)
    for item in findings:
        print(f"- [{item.rule}] {item.path}: {item.detail}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check git candidates for unsafe assets")
    parser.add_argument(
        "--mode",
        choices=("preadd", "staged"),
        default="preadd",
        help="`preadd` checks changed files before git add, `staged` checks staged files",
    )
    parser.add_argument("--max-size-mb", type=float, default=10.0, help="Max allowed file size in MB")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        candidates = list_candidate_files(args.mode)
    except subprocess.CalledProcessError as exc:
        print(f"[repo-guard] git command failed: {exc}", file=sys.stderr)
        return 2

    violations, warnings = evaluate_paths(candidates, args.mode, args.max_size_mb)
    print(f"[repo-guard] mode={args.mode} candidates={len(candidates)} threshold={args.max_size_mb:.2f}MB")

    if warnings:
        print_findings("[repo-guard] warnings", warnings)

    if violations:
        print_findings("[repo-guard] violations", violations)
        print("[repo-guard] failed")
        return 1

    print("[repo-guard] passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
