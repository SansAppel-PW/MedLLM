#!/usr/bin/env python3
"""Resilient HuggingFace model prefetch with retries.

Uses per-file `hf_hub_download` to avoid occasional `snapshot_download`
locking stalls on large multi-shard models.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Iterable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prefetch HF model snapshot with retries.")
    parser.add_argument("--repo-id", required=True, help="Model repo id, e.g. Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--sleep-seconds", type=int, default=30)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--allow-patterns", default="*.json,*.safetensors,*.txt,tokenizer*,*.model,*.py")
    parser.add_argument("--require-safetensors", action="store_true")
    return parser


def parse_patterns(raw: str) -> list[str] | None:
    out = [item.strip() for item in (raw or "").split(",") if item.strip()]
    return out or None


def parse_allow_extensions(patterns: list[str] | None) -> set[str]:
    exts: set[str] = set()
    for item in patterns or []:
        item = item.strip()
        if item.startswith("*."):
            exts.add(item[1:])  # keep leading dot
    return exts


def should_include_file(filename: str, allowed_exts: set[str]) -> bool:
    if not allowed_exts:
        return True
    path = Path(filename)
    if path.suffix in allowed_exts:
        return True
    lower = path.name.lower()
    if lower.startswith("tokenizer"):
        return True
    return False


def to_snapshot_path(local_path: str) -> str | None:
    marker = "/snapshots/"
    if marker not in local_path:
        return None
    return local_path


def iter_small_candidate_files(allowed_exts: set[str]) -> Iterable[str]:
    candidates = [
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
        "special_tokens_map.json",
        "qwen.tiktoken",
        "vocab.json",
        "merges.txt",
        "README.md",
    ]
    for item in candidates:
        if should_include_file(item, allowed_exts):
            yield item


def download_one_file(
    *,
    repo_id: str,
    revision: str,
    filename: str,
    retries: int,
    sleep_seconds: int,
    required: bool,
) -> str | None:
    from huggingface_hub import hf_hub_download

    last_error: str | None = None
    for idx in range(1, max(1, retries) + 1):
        try:
            return hf_hub_download(
                repo_id=repo_id,
                revision=revision,
                filename=filename,
                resume_download=True,
            )
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"
            last_error = err
            if (not required) and ("RemoteEntryNotFoundError" in err):
                print(
                    json.dumps(
                        {"status": "skip_optional", "file": filename, "error": err},
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                return None
            print(
                json.dumps(
                    {
                        "status": "retry",
                        "file": filename,
                        "attempt": idx,
                        "error": err,
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            if idx < retries:
                time.sleep(max(1, sleep_seconds))

    if required:
        raise RuntimeError(f"Failed to download required file: {filename}; last_error={last_error}")
    print(
        json.dumps(
            {"status": "skip_optional", "file": filename, "error": last_error},
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return None


def run_once(
    repo_id: str,
    revision: str,
    retries: int,
    sleep_seconds: int,
    allow_patterns: list[str] | None,
    require_safetensors: bool,
) -> dict[str, object]:
    allowed_exts = parse_allow_extensions(allow_patterns)
    downloaded: list[str] = []
    snapshots: list[str] = []

    # First ensure the index exists, then derive exact shard file names.
    index_local = download_one_file(
        repo_id=repo_id,
        revision=revision,
        filename="model.safetensors.index.json",
        retries=retries,
        sleep_seconds=sleep_seconds,
        required=True,
    )
    assert index_local is not None
    downloaded.append(index_local)
    snap_path = to_snapshot_path(index_local)
    if snap_path:
        snapshots.append(str(Path(snap_path).parent))

    index = json.loads(Path(index_local).read_text(encoding="utf-8"))
    weight_map: dict[str, str] = dict(index.get("weight_map", {}))
    shard_files = sorted(set(weight_map.values()))

    # Pull small config/tokenizer files first (best effort for optional files).
    for small_file in iter_small_candidate_files(allowed_exts):
        local_file = download_one_file(
            repo_id=repo_id,
            revision=revision,
            filename=small_file,
            retries=retries,
            sleep_seconds=sleep_seconds,
            required=(small_file in {"config.json", "tokenizer_config.json"}),
        )
        if local_file:
            downloaded.append(local_file)
            snap = to_snapshot_path(local_file)
            if snap:
                snapshots.append(str(Path(snap).parent))

    # Pull all shard files sequentially to avoid multi-worker lock stalls.
    for shard in shard_files:
        if not should_include_file(shard, allowed_exts):
            continue
        local_file = download_one_file(
            repo_id=repo_id,
            revision=revision,
            filename=shard,
            retries=retries,
            sleep_seconds=sleep_seconds,
            required=True,
        )
        if local_file:
            downloaded.append(local_file)
            snap = to_snapshot_path(local_file)
            if snap:
                snapshots.append(str(Path(snap).parent))

    snap_dir = Path(sorted(set(snapshots))[0]) if snapshots else Path(index_local).parent
    safetensor_count = len(list(snap_dir.glob("*.safetensors")))
    if require_safetensors and safetensor_count <= 0:
        raise RuntimeError("No .safetensors found in downloaded snapshot.")
    if require_safetensors and safetensor_count < len(shard_files):
        raise RuntimeError(
            f"Expected {len(shard_files)} shard files, but snapshot has {safetensor_count}."
        )

    payload: dict[str, object] = {
        "snapshot_dir": str(snap_dir),
        "safetensors": safetensor_count,
        "expected_shards": len(shard_files),
        "downloaded_files": len(downloaded),
    }
    return payload


def main() -> int:
    args = build_parser().parse_args()
    allow_patterns = parse_patterns(args.allow_patterns)

    print(
        json.dumps(
            {
                "repo_id": args.repo_id,
                "revision": args.revision,
                "hf_endpoint": os.getenv("HF_ENDPOINT"),
                "hf_hub_disable_xet": os.getenv("HF_HUB_DISABLE_XET"),
                "hf_hub_download_timeout": os.getenv("HF_HUB_DOWNLOAD_TIMEOUT"),
                "hf_hub_etag_timeout": os.getenv("HF_HUB_ETAG_TIMEOUT"),
                "retries": args.retries,
                "sleep_seconds": args.sleep_seconds,
                "max_workers": args.max_workers,
            },
            ensure_ascii=False,
        )
    )

    last_error: str | None = None
    for idx in range(1, max(1, args.retries) + 1):
        try:
            payload = run_once(
                repo_id=args.repo_id,
                revision=args.revision,
                retries=max(1, args.retries),
                sleep_seconds=max(1, args.sleep_seconds),
                allow_patterns=allow_patterns,
                require_safetensors=args.require_safetensors,
            )
            payload["attempt"] = idx
            payload["status"] = "ok"
            print(json.dumps(payload, ensure_ascii=False))
            return 0
        except Exception as exc:  # noqa: BLE001
            last_error = f"{type(exc).__name__}: {exc}"
            print(
                json.dumps(
                    {
                        "status": "retry",
                        "attempt": idx,
                        "error": last_error,
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            if idx < args.retries:
                time.sleep(max(1, args.sleep_seconds))

    print(
        json.dumps(
            {"status": "failed", "repo_id": args.repo_id, "error": last_error},
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
