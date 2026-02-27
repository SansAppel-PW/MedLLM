#!/usr/bin/env python3
"""Build thesis-grade real datasets from HuggingFace datasets-server.

Outputs:
- data/raw/real_sources/*.jsonl
- data/clean/real_sft_train.jsonl
- data/clean/real_sft_dev.jsonl
- data/clean/real_sft_test.jsonl
- data/benchmark/real_medqa_benchmark.jsonl
- reports/real_dataset_report.md
- reports/real_dataset_summary.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from urllib.error import HTTPError
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROWS_API = "https://datasets-server.huggingface.co/rows"


@dataclass(frozen=True)
class SourceSpec:
    name: str
    dataset: str
    config: str
    split: str
    target_count: int
    adapter: str
    license_hint: str


def http_get_json(
    url: str,
    retries: int = 8,
    sleep_sec: float = 1.5,
    rate_limit_sleep: float = 20.0,
) -> dict[str, Any]:
    last_err: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "medllm-data-builder/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except HTTPError as err:
            last_err = err
            if err.code == 429 and i < retries - 1:
                # Rate-limit backoff
                wait = rate_limit_sleep * (i + 1)
                print(f"[warn] 429 rate limited, sleep {wait:.1f}s then retry")
                time.sleep(wait)
                continue
            if i < retries - 1:
                time.sleep(sleep_sec * (i + 1))
            else:
                raise
        except Exception as err:  # noqa: BLE001
            last_err = err
            if i < retries - 1:
                time.sleep(sleep_sec * (i + 1))
            else:
                raise
    assert last_err is not None
    raise last_err


def rows_url(dataset: str, config: str, split: str, offset: int, length: int) -> str:
    q = urllib.parse.urlencode(
        {
            "dataset": dataset,
            "config": config,
            "split": split,
            "offset": offset,
            "length": length,
        }
    )
    return f"{ROWS_API}?{q}"


def get_num_rows(dataset: str, config: str, split: str) -> int:
    data = http_get_json(rows_url(dataset, config, split, 0, 1))
    return int(data.get("num_rows_total", 0))


def fetch_rows(
    dataset: str,
    config: str,
    split: str,
    offset: int,
    length: int,
    request_interval: float = 0.25,
) -> list[dict[str, Any]]:
    if request_interval > 0:
        time.sleep(request_interval)
    data = http_get_json(rows_url(dataset, config, split, offset, length))
    rows = []
    for item in data.get("rows", []):
        row = item.get("row", {})
        if isinstance(row, dict):
            rows.append(row)
    return rows


def flatten_questions(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for x in value:
            if isinstance(x, list):
                parts.extend([str(y).strip() for y in x if str(y).strip()])
            else:
                txt = str(x).strip()
                if txt:
                    parts.append(txt)
        return "\n".join(parts)
    return str(value).strip()


def adapt_cmt(row: dict[str, Any], idx: int) -> dict[str, Any] | None:
    instruction = str(row.get("instruction", "") or "").strip()
    answer = str(row.get("output", "") or "").strip()
    if not instruction or not answer:
        return None

    input_text = str(row.get("input", "") or "").strip()
    query = instruction if not input_text else f"{instruction}\n补充信息: {input_text}"

    history = row.get("history", [])
    context_lines = []
    if isinstance(history, list):
        for turn in history:
            if isinstance(turn, list) and len(turn) >= 2:
                user = str(turn[0]).strip()
                assistant = str(turn[1]).strip()
                if user:
                    context_lines.append(f"用户: {user}")
                if assistant:
                    context_lines.append(f"医生: {assistant}")
    context = "\n".join(context_lines)

    return {
        "id": f"cmt_{idx:08d}",
        "query": query,
        "context": context,
        "answer": answer,
        "meta": {
            "source_dataset": "Suprit/CMtMedQA",
            "source_id": row.get("id"),
            "cate1": row.get("cate1"),
            "cate2": row.get("cate2"),
            "language": "zh",
        },
    }


def adapt_huatuo26(row: dict[str, Any], idx: int) -> dict[str, Any] | None:
    query = str(row.get("question", "") or "").strip()
    answer = str(row.get("answer", "") or "").strip()
    if not query or not answer:
        return None

    context_items = []
    label = str(row.get("label", "") or "").strip()
    disease = str(row.get("related_diseases", "") or "").strip()
    if label:
        context_items.append(f"科室标签: {label}")
    if disease:
        context_items.append(f"相关疾病: {disease}")

    return {
        "id": f"h26_{idx:08d}",
        "query": query,
        "context": "\n".join(context_items),
        "answer": answer,
        "meta": {
            "source_dataset": "FreedomIntelligence/Huatuo26M-Lite",
            "source_id": row.get("id"),
            "score": row.get("score"),
            "label": label,
            "language": "zh",
        },
    }


def adapt_huatuo_enc(row: dict[str, Any], idx: int) -> dict[str, Any] | None:
    query = flatten_questions(row.get("questions", ""))
    answers = row.get("answers", [])
    if isinstance(answers, list):
        answer = str(answers[0]).strip() if answers else ""
    else:
        answer = str(answers).strip()

    if not query or not answer:
        return None

    return {
        "id": f"henc_{idx:08d}",
        "query": query,
        "context": "",
        "answer": answer,
        "meta": {
            "source_dataset": "FreedomIntelligence/huatuo_encyclopedia_qa",
            "language": "zh",
        },
    }


def adapt_medqa(row: dict[str, Any], idx: int) -> dict[str, Any] | None:
    stem = str(row.get("sent1", "") or "").strip()
    sent2 = str(row.get("sent2", "") or "").strip()
    endings = [str(row.get(f"ending{i}", "") or "").strip() for i in range(4)]
    if not stem or not all(endings):
        return None

    query = stem
    if sent2:
        query += f"\n{sent2}"
    query += "\n选项:\n"
    query += "\n".join([f"{chr(65+i)}. {endings[i]}" for i in range(4)])

    label = int(row.get("label", 0))
    label = label if 0 <= label < 4 else 0
    correct = endings[label]

    wrong = [endings[i] for i in range(4) if i != label]

    return {
        "id": f"medqa_{idx:08d}",
        "query": query,
        "context": "",
        "answer": f"正确答案: {chr(65+label)}. {correct}",
        "meta": {
            "source_dataset": "GBaker/MedQA-USMLE-4-options-hf",
            "source_id": row.get("id"),
            "label": label,
            "wrong_options": wrong,
            "language": "en",
        },
    }


ADAPTERS: dict[str, Callable[[dict[str, Any], int], dict[str, Any] | None]] = {
    "cmt": adapt_cmt,
    "huatuo26": adapt_huatuo26,
    "huatuo_enc": adapt_huatuo_enc,
    "medqa": adapt_medqa,
}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for row in rows:
        key = hashlib.md5((row.get("query", "") + "\n" + row.get("answer", "")).encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def split_rows(rows: list[dict[str, Any]], seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    data = rows[:]
    rng.shuffle(data)
    n = len(data)
    if n == 0:
        return [], [], []
    if n < 3:
        return data, [], []

    # For large-scale builds keep >=1000 dev/test; for small-scale smoke builds keep non-zero train/dev/test.
    min_split = 1000 if n >= 15000 else 1
    n_test = max(min_split, int(n * 0.1))
    n_dev = max(min_split, int(n * 0.1))

    if n_dev + n_test >= n:
        n_dev = max(1, n // 10)
        n_test = max(1, n // 10)
    if n_dev + n_test >= n:
        n_dev = 1
        n_test = 1

    n_train = max(1, n - n_dev - n_test)
    n_dev = min(n_dev, n - n_train - 1)
    n_test = n - n_train - n_dev

    train = data[:n_train]
    dev = data[n_train : n_train + n_dev]
    test = data[n_train + n_dev :]
    return train, dev, test


def fetch_source(
    spec: SourceSpec,
    seed: int,
    request_interval: float = 0.25,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    adapter = ADAPTERS[spec.adapter]
    total = get_num_rows(spec.dataset, spec.config, spec.split)

    if spec.target_count <= 0:
        target = total
    else:
        target = min(spec.target_count, total)

    rng = random.Random((seed + sum(ord(c) for c in spec.dataset)) % (2**31 - 1))
    start_max = max(0, total - target)
    start = rng.randint(0, start_max) if start_max > 0 else 0

    page = 100
    rows: list[dict[str, Any]] = []
    cursor = start
    idx = 0

    while len(rows) < target:
        length = min(page, target - len(rows))
        batch = fetch_rows(
            spec.dataset,
            spec.config,
            spec.split,
            cursor,
            length,
            request_interval=request_interval,
        )
        if not batch:
            break

        for item in batch:
            converted = adapter(item, idx)
            idx += 1
            if converted is not None:
                rows.append(converted)

        cursor += len(batch)
        if len(rows) % 1000 == 0:
            print(f"[{spec.name}] progress={len(rows)}/{target}")

    summary = {
        "name": spec.name,
        "dataset": spec.dataset,
        "config": spec.config,
        "split": spec.split,
        "num_rows_total": total,
        "start_offset": start,
        "target_count": target,
        "fetched_count": len(rows),
        "license": spec.license_hint,
    }
    return rows, summary


def build_medqa_benchmark(seed: int, train_n: int, val_n: int, test_n: int) -> list[dict[str, Any]]:
    medqa_spec = [
        ("train", train_n),
        ("validation", val_n),
        ("test", test_n),
    ]

    benchmark: list[dict[str, Any]] = []
    rng = random.Random(seed + 2026)

    for split, n in medqa_spec:
        total = get_num_rows("GBaker/MedQA-USMLE-4-options-hf", "default", split)
        target = min(n, total)
        start_max = max(0, total - target)
        start = rng.randint(0, start_max) if start_max > 0 else 0

        fetched = 0
        offset = start
        while fetched < target:
            batch = fetch_rows(
                "GBaker/MedQA-USMLE-4-options-hf",
                "default",
                split,
                offset,
                min(100, target - fetched),
                request_interval=0.25,
            )
            if not batch:
                break
            for row in batch:
                sample = adapt_medqa(row, fetched)
                if sample is None:
                    continue
                wrong_options = sample["meta"].get("wrong_options", [])
                if not wrong_options:
                    continue

                low = {
                    "id": f"medqa_{split}_{fetched:06d}_pos",
                    "query": sample["query"],
                    "answer": sample["answer"],
                    "expected_risk": "low",
                    "meta": {
                        "source_dataset": "GBaker/MedQA-USMLE-4-options-hf",
                        "split": split,
                    },
                }
                wrong = rng.choice(wrong_options)
                high = {
                    "id": f"medqa_{split}_{fetched:06d}_neg",
                    "query": sample["query"],
                    "answer": f"正确答案: {wrong}",
                    "expected_risk": "high",
                    "meta": {
                        "source_dataset": "GBaker/MedQA-USMLE-4-options-hf",
                        "split": split,
                        "construction": "incorrect_option_adversarial",
                    },
                }
                benchmark.extend([low, high])
                fetched += 1
                if fetched >= target:
                    break
            offset += len(batch)

    return benchmark


def save_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 真实数据集构建报告",
        "",
        "## 数据源",
        "| 名称 | 数据集 | split | 总规模 | 采样起点 | 采样量 | 许可 |",
        "|---|---|---|---:|---:|---:|---|",
    ]

    for s in summary["sources"]:
        lines.append(
            f"| {s['name']} | {s['dataset']} | {s['split']} | {s['num_rows_total']} | {s['start_offset']} | {s['fetched_count']} | {s['license']} |"
        )

    lines.extend(
        [
            "",
            "## 合并与切分",
            f"- 合并后样本数（去重前）: {summary['merged_before_dedup']}",
            f"- 合并后样本数（去重后）: {summary['merged_after_dedup']}",
            f"- 训练集: {summary['train_count']}",
            f"- 验证集: {summary['dev_count']}",
            f"- 测试集: {summary['test_count']}",
            "",
            "## Benchmark",
            f"- real_medqa_benchmark 样本数: {summary['benchmark_count']}（含正例与对抗负例）",
            "",
            "## 产物",
            "- `data/raw/real_sources/*.jsonl`",
            "- `data/clean/real_sft_train.jsonl`",
            "- `data/clean/real_sft_dev.jsonl`",
            "- `data/clean/real_sft_test.jsonl`",
            "- `data/benchmark/real_medqa_benchmark.jsonl`",
        ]
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build real dataset package for thesis")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cmt-count", type=int, default=20000)
    parser.add_argument("--h26-count", type=int, default=15000)
    parser.add_argument("--henc-count", type=int, default=15000)
    parser.add_argument("--bench-train", type=int, default=2000)
    parser.add_argument("--bench-val", type=int, default=600)
    parser.add_argument("--bench-test", type=int, default=600)
    parser.add_argument("--request-interval", type=float, default=0.25)
    parser.add_argument("--benchmark-out", default="data/benchmark/real_medqa_benchmark.jsonl")
    parser.add_argument("--summary-out", default="reports/real_dataset_summary.json")
    parser.add_argument("--report-out", default="reports/real_dataset_report.md")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]

    specs = [
        SourceSpec(
            name="cmtmedqa",
            dataset="Suprit/CMtMedQA",
            config="default",
            split="train",
            target_count=args.cmt_count,
            adapter="cmt",
            license_hint="MIT",
        ),
        SourceSpec(
            name="huatuo26m_lite",
            dataset="FreedomIntelligence/Huatuo26M-Lite",
            config="default",
            split="train",
            target_count=args.h26_count,
            adapter="huatuo26",
            license_hint="Apache-2.0",
        ),
        SourceSpec(
            name="huatuo_encyclopedia",
            dataset="FreedomIntelligence/huatuo_encyclopedia_qa",
            config="default",
            split="train",
            target_count=args.henc_count,
            adapter="huatuo_enc",
            license_hint="Apache-2.0",
        ),
    ]

    all_rows: list[dict[str, Any]] = []
    source_summaries = []

    for spec in specs:
        rows, summary = fetch_source(spec, seed=args.seed, request_interval=args.request_interval)
        source_summaries.append(summary)
        all_rows.extend(rows)
        out_path = root / "data/raw/real_sources" / f"{spec.name}.jsonl"
        write_jsonl(out_path, rows)
        print(f"[saved] {out_path} rows={len(rows)}")

    merged_before = len(all_rows)
    deduped = deduplicate(all_rows)
    merged_after = len(deduped)

    write_jsonl(root / "data/raw/real_sources/merged_real_qa.jsonl", deduped)

    train, dev, test = split_rows(deduped, seed=args.seed)
    write_jsonl(root / "data/clean/real_sft_train.jsonl", train)
    write_jsonl(root / "data/clean/real_sft_dev.jsonl", dev)
    write_jsonl(root / "data/clean/real_sft_test.jsonl", test)

    benchmark = build_medqa_benchmark(
        seed=args.seed,
        train_n=args.bench_train,
        val_n=args.bench_val,
        test_n=args.bench_test,
    )
    write_jsonl(root / args.benchmark_out, benchmark)

    summary = {
        "sources": source_summaries,
        "merged_before_dedup": merged_before,
        "merged_after_dedup": merged_after,
        "train_count": len(train),
        "dev_count": len(dev),
        "test_count": len(test),
        "benchmark_count": len(benchmark),
        "seed": args.seed,
    }

    summary_path = root / args.summary_out
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    save_markdown_report(root / args.report_out, summary)
    print("[done] real dataset package built")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
