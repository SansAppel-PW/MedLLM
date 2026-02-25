from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def query_hash(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()


def test_reference_kb_only_uses_train_split(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    benchmark = repo / "data/benchmark/real_medqa_benchmark.jsonl"
    out_kb = tmp_path / "kb.jsonl"
    out_report = tmp_path / "kb_report.md"

    cmd = [
        sys.executable,
        "scripts/data/build_benchmark_reference_kb.py",
        "--benchmark",
        str(benchmark),
        "--include-splits",
        "train",
        "--output",
        str(out_kb),
        "--report",
        str(out_report),
    ]
    subprocess.run(cmd, cwd=repo, check=True)

    train_hashes = set()
    for row in iter_jsonl(benchmark):
        meta = row.get("meta", {})
        split = str(meta.get("split", "")).strip().lower() if isinstance(meta, dict) else ""
        q = str(row.get("query", ""))
        if not q:
            continue
        h = query_hash(q)
        if split == "train":
            train_hashes.add(h)

    kb_rows = list(iter_jsonl(out_kb))
    assert kb_rows, "KB should not be empty for train split"
    kb_hashes = {str(r.get("query_hash", "")) for r in kb_rows}

    assert kb_hashes <= train_hashes
