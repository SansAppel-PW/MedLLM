#!/usr/bin/env python3
"""Resilient HuggingFace model prefetch with retries."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


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


def run_once(
    repo_id: str,
    revision: str,
    max_workers: int,
    allow_patterns: list[str] | None,
) -> dict[str, object]:
    from huggingface_hub import snapshot_download

    snapshot_dir = snapshot_download(
        repo_id=repo_id,
        revision=revision,
        allow_patterns=allow_patterns,
        resume_download=True,
        max_workers=max_workers,
    )
    snapshot_path = Path(snapshot_dir)
    safetensor_count = len(list(snapshot_path.glob("*.safetensors")))
    payload: dict[str, object] = {
        "snapshot_dir": str(snapshot_path),
        "safetensors": safetensor_count,
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
                max_workers=max(1, args.max_workers),
                allow_patterns=allow_patterns,
            )
            if args.require_safetensors and int(payload.get("safetensors", 0)) <= 0:
                raise RuntimeError("No .safetensors found in downloaded snapshot.")
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
