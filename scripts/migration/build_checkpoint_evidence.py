#!/usr/bin/env python3
"""Build lightweight checkpoint evidence manifest without syncing model weights to git."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMPONENT_CANDIDATES = {
    "SFT": [
        "artifacts/remote_v100_20260228/checkpoints/layer_b/qwen25_7b_sft/final",
        "artifacts/remote_v100_20260228/checkpoints/layer_b_qwen25_7b_sft_final",
    ],
    "DPO": [
        "artifacts/remote_v100_20260228/checkpoints/dpo-real-baseline/final",
        "artifacts/remote_v100_20260228/checkpoints/dpo_final",
    ],
    "SimPO": [
        "artifacts/remote_v100_20260228/checkpoints/simpo-real-baseline/final",
        "artifacts/remote_v100_20260228/checkpoints/simpo_final",
    ],
    "KTO": [
        "artifacts/remote_v100_20260228/checkpoints/kto-real-baseline/final",
        "artifacts/remote_v100_20260228/checkpoints/kto_final",
    ],
}

KEY_FILES = [
    "adapter_model.safetensors",
    "adapter_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "README.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pick_existing_dir(root: Path, candidates: list[str]) -> Path | None:
    best: tuple[int, Path] | None = None
    for rel in candidates:
        p = (root / rel).resolve()
        if p.exists() and p.is_dir():
            # Prefer non-empty / richer directories.
            file_count = sum(1 for x in p.rglob("*") if x.is_file())
            score = file_count
            if best is None or score > best[0]:
                best = (score, p)
    return best[1] if best else None


def summarize_dir(path: Path) -> dict[str, Any]:
    file_count = 0
    total_size = 0
    for fp in path.rglob("*"):
        if fp.is_file():
            file_count += 1
            total_size += fp.stat().st_size

    hashes: dict[str, str] = {}
    present_files: list[str] = []
    for name in KEY_FILES:
        fp = path / name
        if fp.exists() and fp.is_file():
            present_files.append(name)
            hashes[name] = sha256_file(fp)

    # Some runs may persist adapter weights with temporary/hidden suffixes.
    if "adapter_model.safetensors" not in present_files:
        alt = sorted(path.glob("*adapter_model*.safetensors*"))
        if alt:
            alias_name = alt[0].name
            present_files.append(alias_name)
            hashes[alias_name] = sha256_file(alt[0])

    return {
        "path": str(path),
        "file_count": file_count,
        "total_size_bytes": total_size,
        "present_key_files": present_files,
        "key_file_sha256": hashes,
        "verified": bool(present_files),
    }


def build_manifest(root: Path) -> dict[str, Any]:
    components: dict[str, Any] = {}
    all_verified = True
    for name, candidates in COMPONENT_CANDIDATES.items():
        chosen = pick_existing_dir(root, candidates)
        if chosen is None:
            components[name] = {
                "verified": False,
                "path": "",
                "file_count": 0,
                "total_size_bytes": 0,
                "present_key_files": [],
                "key_file_sha256": {},
                "candidates": candidates,
            }
            all_verified = False
            continue
        item = summarize_dir(chosen)
        item["candidates"] = candidates
        components[name] = item
        if not item["verified"]:
            all_verified = False

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "components": components,
        "all_verified": all_verified,
        "note": "Evidence manifest for external checkpoints (weights may be intentionally excluded from git).",
    }


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Checkpoint Evidence Manifest",
        "",
        f"- generated_at_utc: {manifest.get('generated_at_utc')}",
        f"- all_verified: {manifest.get('all_verified')}",
        f"- root: `{manifest.get('root')}`",
        "",
        "| Component | Verified | Path | Key Files | Size (MB) |",
        "|---|---|---|---|---:|",
    ]
    for name in ["SFT", "DPO", "SimPO", "KTO"]:
        item = manifest["components"].get(name, {})
        size_mb = float(item.get("total_size_bytes", 0)) / (1024 * 1024)
        key_files = ", ".join(item.get("present_key_files", []))
        lines.append(
            f"| {name} | {item.get('verified', False)} | {item.get('path', '')} | {key_files} | {size_mb:.2f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build external checkpoint evidence manifest")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-json", default="reports/training/checkpoint_evidence.json")
    parser.add_argument("--output-md", default="reports/training/checkpoint_evidence.md")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = build_manifest(root)

    out_json = (root / args.output_json).resolve()
    out_md = (root / args.output_md).resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(out_md, manifest)

    print(json.dumps({"all_verified": manifest["all_verified"], "output_json": str(out_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
