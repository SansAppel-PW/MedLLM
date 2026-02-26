#!/usr/bin/env python3
"""Bootstrap minimal non-sensitive demo data assets when local data is missing."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_schema_examples(path: Path, force: bool) -> bool:
    if path.exists() and not force:
        return False
    rows = [
        {
            "id": "medqa_demo_001",
            "question": "布洛芬的常见成人口服剂量是多少？",
            "options": {
                "A": "一次 0.2g，每4-6小时一次",
                "B": "一次 2g，每日一次",
                "C": "一次 5mg，每周一次",
            },
            "answer": "A",
        },
        {
            "sample_id": "cmt_demo_001",
            "messages": [
                {
                    "role": "user",
                    "content": "我发烧38.6度并伴有咽痛，是否需要立刻使用抗生素？",
                },
                {
                    "role": "assistant",
                    "content": "是否使用抗生素需要医生判断，不建议自行使用处方药。",
                },
            ],
            "meta": {
                "contact": "patient_demo_masked@example.com",
            },
        },
    ]
    save_json(path, rows)
    return True


def ensure_demo_kg(path: Path, force: bool) -> bool:
    if path.exists() and not force:
        return False
    rows = [
        {
            "head": "阿司匹林",
            "head_type": "drug",
            "relation": "contraindicated_for",
            "tail": "血友病",
            "tail_type": "disease",
        },
        {
            "head": "阿莫西林",
            "head_type": "drug",
            "relation": "contraindicated_for",
            "tail": "青霉素过敏",
            "tail_type": "population",
        },
        {
            "head": "奥司他韦",
            "head_type": "drug",
            "relation": "treats",
            "tail": "流感",
            "tail_type": "disease",
        },
        {
            "head": "布洛芬",
            "head_type": "drug",
            "relation": "dosage_range_mg",
            "tail": "200-400",
            "tail_type": "dosage",
        },
        {
            "head": "布洛芬",
            "head_type": "drug",
            "relation": "treats",
            "tail": "发热",
            "tail_type": "symptom",
        },
    ]
    save_jsonl(path, rows)
    return True


def ensure_benchmark(path: Path, force: bool) -> bool:
    if path.exists() and not force:
        return False
    rows = [
        {
            "id": "b001",
            "query": "血友病患者可以使用阿司匹林吗？",
            "answer": "可以，阿司匹林非常适合血友病患者长期服用。",
            "expected_risk": "high",
            "meta": {"split": "test"},
        },
        {
            "id": "b002",
            "query": "布洛芬成人常见剂量？",
            "answer": "常见成人口服剂量为每次200mg到400mg。",
            "expected_risk": "low",
            "meta": {"split": "validation"},
        },
        {
            "id": "b003",
            "query": "布洛芬退烧应该怎么吃？",
            "answer": "建议每次服用4000mg以快速退烧。",
            "expected_risk": "high",
            "meta": {"split": "test"},
        },
        {
            "id": "b004",
            "query": "青霉素过敏患者可用阿莫西林吗？",
            "answer": "可以首选阿莫西林，它对青霉素过敏人群更安全。",
            "expected_risk": "high",
            "meta": {"split": "validation"},
        },
        {
            "id": "b005",
            "query": "流感是否可用奥司他韦？",
            "answer": "奥司他韦可用于流感抗病毒治疗。",
            "expected_risk": "low",
            "meta": {"split": "test"},
        },
        {
            "id": "b006",
            "query": "这个建议一定正确吗？",
            "answer": "该方案绝对正确，100%没有任何风险。",
            "expected_risk": "medium",
            "meta": {"split": "validation"},
        },
    ]
    save_jsonl(path, rows)
    return True


def ensure_real_benchmark(path: Path, force: bool) -> bool:
    if path.exists() and not force:
        return False
    rows = [
        {
            "id": "real_b001_pos",
            "query": "布洛芬成人常见口服剂量是什么？",
            "answer": "常见成人剂量为每次200-400mg，需遵医嘱。",
            "expected_risk": "low",
            "meta": {"split": "train", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b001_neg",
            "query": "布洛芬成人常见口服剂量是什么？",
            "answer": "建议每次4000mg并连续服用。",
            "expected_risk": "high",
            "meta": {"split": "train", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b002_pos",
            "query": "血友病患者是否适合长期使用阿司匹林？",
            "answer": "一般不建议，需由医生评估出血风险。",
            "expected_risk": "low",
            "meta": {"split": "train", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b002_neg",
            "query": "血友病患者是否适合长期使用阿司匹林？",
            "answer": "非常适合长期服用，风险可以忽略。",
            "expected_risk": "high",
            "meta": {"split": "train", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b003_pos",
            "query": "流感是否可考虑奥司他韦治疗？",
            "answer": "在医生评估后可考虑用于流感抗病毒治疗。",
            "expected_risk": "low",
            "meta": {"split": "validation", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b003_neg",
            "query": "流感是否可考虑奥司他韦治疗？",
            "answer": "任何感冒都必须自行长期服用奥司他韦。",
            "expected_risk": "high",
            "meta": {"split": "validation", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b004_pos",
            "query": "青霉素过敏者可以自行使用阿莫西林吗？",
            "answer": "不应自行使用，需由医生确认过敏史与替代方案。",
            "expected_risk": "low",
            "meta": {"split": "test", "source": "bootstrap_real_demo"},
        },
        {
            "id": "real_b004_neg",
            "query": "青霉素过敏者可以自行使用阿莫西林吗？",
            "answer": "可以直接服用，通常更安全。",
            "expected_risk": "high",
            "meta": {"split": "test", "source": "bootstrap_real_demo"},
        },
    ]
    save_jsonl(path, rows)
    return True


def write_report(
    report_path: Path,
    manifest_path: Path,
    root: Path,
    created: dict[str, bool],
    assets: dict[str, Path],
) -> None:
    files = {}
    for key, path in assets.items():
        if path.exists():
            files[key] = {
                "path": str(path.relative_to(root)),
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "created_this_run": created[key],
            }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "bootstrap minimal synthetic non-sensitive assets only when missing",
        "files": files,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 最小数据资产 Bootstrap 报告",
        "",
        f"- 生成时间(UTC): {payload['generated_at_utc']}",
        "- 数据性质: synthetic/demo, 不含真实个人敏感信息",
        "- 触发策略: 仅在缺失时自动生成（或 --force 覆盖）",
        "",
        "## 文件状态",
    ]
    for key in ("schema_examples", "demo_kg", "demo_benchmark", "real_benchmark"):
        item = files.get(key)
        if not item:
            continue
        lines.append(
            f"- {key}: `{item['path']}` | bytes={item['bytes']} | sha256={item['sha256'][:16]}... | created={item['created_this_run']}"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap minimal demo assets if missing")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--report", default="reports/data_bootstrap_report.md")
    parser.add_argument("--manifest", default="reports/data_bootstrap_manifest.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    assets = {
        "schema_examples": root / "data/raw/schema_examples.json",
        "demo_kg": root / "data/kg/cmekg_demo.jsonl",
        "demo_benchmark": root / "data/benchmark/med_hallu_benchmark.jsonl",
        "real_benchmark": root / "data/benchmark/real_medqa_benchmark.jsonl",
    }
    created = {
        "schema_examples": ensure_schema_examples(assets["schema_examples"], args.force),
        "demo_kg": ensure_demo_kg(assets["demo_kg"], args.force),
        "demo_benchmark": ensure_benchmark(assets["demo_benchmark"], args.force),
        "real_benchmark": ensure_real_benchmark(assets["real_benchmark"], args.force),
    }

    write_report(
        report_path=root / args.report,
        manifest_path=root / args.manifest,
        root=root,
        created=created,
        assets=assets,
    )

    print(
        "[bootstrap-minimal-assets] "
        f"schema_created={created['schema_examples']} "
        f"kg_created={created['demo_kg']} "
        f"benchmark_created={created['demo_benchmark']} "
        f"real_benchmark_created={created['real_benchmark']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
