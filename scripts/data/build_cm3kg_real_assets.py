#!/usr/bin/env python3
"""Build real training/eval assets from local CM3KG dataset.

Inputs (under CM3KG):
- medical.csv
- Disease.csv

Outputs:
- data/clean/real_sft_{train,dev,test}.jsonl
- data/benchmark/real_medqa_benchmark.jsonl
- data/kg/cm3kg_core_kb.jsonl
- reports/real_dataset_summary.json
- reports/real_dataset_report.md
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

import pandas as pd


def parse_list_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "[]"}:
        return []
    try:
        parsed = ast.literal_eval(text)
    except Exception:  # noqa: BLE001
        parsed = None
    if isinstance(parsed, list):
        return [str(x).strip() for x in parsed if str(x).strip()]
    return [x.strip() for x in re.split(r"[、,，;；\s]+", text) if x.strip()]


def short_text(text: str, max_len: int = 220) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_sft_rows(med_df: pd.DataFrame, max_rows: int, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rng = random.Random(seed)

    for _, rec in med_df.iterrows():
        disease = str(rec.get("name", "") or "").strip()
        if not disease:
            continue
        category = parse_list_field(rec.get("category"))
        cure_department = parse_list_field(rec.get("cure_department"))
        context = f"疾病: {disease}; 分类: {'/'.join(category[:3])}; 科室: {'/'.join(cure_department[:3])}"

        desc = short_text(str(rec.get("desc", "") or ""))
        if desc:
            rows.append(
                {
                    "id": f"cm3kg_{len(rows):08d}",
                    "query": f"{disease}是什么？",
                    "context": context,
                    "answer": desc,
                    "meta": {"source_dataset": "CM3KG/medical.csv", "field": "desc", "language": "zh"},
                }
            )

        symptoms = parse_list_field(rec.get("symptom"))
        if symptoms:
            rows.append(
                {
                    "id": f"cm3kg_{len(rows):08d}",
                    "query": f"{disease}常见症状有哪些？",
                    "context": context,
                    "answer": f"常见症状包括：{'、'.join(symptoms[:8])}。",
                    "meta": {"source_dataset": "CM3KG/medical.csv", "field": "symptom", "language": "zh"},
                }
            )

        checks = parse_list_field(rec.get("check"))
        if checks:
            rows.append(
                {
                    "id": f"cm3kg_{len(rows):08d}",
                    "query": f"{disease}通常需要做哪些检查？",
                    "context": context,
                    "answer": f"常见检查包括：{'、'.join(checks[:8])}。",
                    "meta": {"source_dataset": "CM3KG/medical.csv", "field": "check", "language": "zh"},
                }
            )

        drugs = parse_list_field(rec.get("recommand_drug")) + parse_list_field(rec.get("common_drug"))
        drugs = list(dict.fromkeys(drugs))
        if drugs:
            rows.append(
                {
                    "id": f"cm3kg_{len(rows):08d}",
                    "query": f"{disease}常用药物有哪些？",
                    "context": context,
                    "answer": f"常见药物包括：{'、'.join(drugs[:10])}。具体用药需遵医嘱。",
                    "meta": {"source_dataset": "CM3KG/medical.csv", "field": "recommand_drug/common_drug", "language": "zh"},
                }
            )

        prevent = short_text(str(rec.get("prevent", "") or ""))
        if prevent:
            rows.append(
                {
                    "id": f"cm3kg_{len(rows):08d}",
                    "query": f"如何预防{disease}？",
                    "context": context,
                    "answer": prevent,
                    "meta": {"source_dataset": "CM3KG/medical.csv", "field": "prevent", "language": "zh"},
                }
            )

        cure_way = parse_list_field(rec.get("cure_way"))
        if cure_way:
            rows.append(
                {
                    "id": f"cm3kg_{len(rows):08d}",
                    "query": f"{disease}通常如何治疗？",
                    "context": context,
                    "answer": f"常见治疗方式：{'、'.join(cure_way[:6])}。",
                    "meta": {"source_dataset": "CM3KG/medical.csv", "field": "cure_way", "language": "zh"},
                }
            )

    # Deduplicate to avoid near-duplicate templates.
    dedup = []
    seen = set()
    for row in rows:
        key = hashlib.md5((row["query"] + "\n" + row["answer"]).encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)

    rng.shuffle(dedup)
    if max_rows > 0 and len(dedup) > max_rows:
        dedup = dedup[:max_rows]
    return dedup


def split_rows(rows: list[dict[str, Any]], seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    data = rows[:]
    rng.shuffle(data)
    n = len(data)
    if n <= 2:
        return data, [], []
    n_dev = max(1, int(n * 0.1))
    n_test = max(1, int(n * 0.1))
    if n_dev + n_test >= n:
        n_dev, n_test = 1, 1
    n_train = n - n_dev - n_test
    return data[:n_train], data[n_train : n_train + n_dev], data[n_train + n_dev :]


def build_benchmark(med_df: pd.DataFrame, max_pairs: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed + 7)
    disease_to_drugs: dict[str, list[str]] = {}
    disease_to_symptoms: dict[str, list[str]] = {}
    disease_to_checks: dict[str, list[str]] = {}
    all_drugs: list[str] = []
    all_symptoms: list[str] = []

    for _, rec in med_df.iterrows():
        disease = str(rec.get("name", "") or "").strip()
        if not disease:
            continue
        drugs = list(
            dict.fromkeys(parse_list_field(rec.get("recommand_drug")) + parse_list_field(rec.get("common_drug")))
        )
        symptoms = parse_list_field(rec.get("symptom"))
        checks = parse_list_field(rec.get("check"))
        if drugs:
            disease_to_drugs[disease] = drugs
            all_drugs.extend(drugs)
        if symptoms:
            disease_to_symptoms[disease] = symptoms
            all_symptoms.extend(symptoms)
        if checks:
            disease_to_checks[disease] = checks

    all_drugs = list(dict.fromkeys([x for x in all_drugs if x]))
    all_symptoms = list(dict.fromkeys([x for x in all_symptoms if x]))

    diseases = sorted(set(disease_to_drugs) | set(disease_to_symptoms) | set(disease_to_checks))
    rng.shuffle(diseases)
    if max_pairs > 0:
        diseases = diseases[:max_pairs]

    out: list[dict[str, Any]] = []
    for i, disease in enumerate(diseases):
        if i % 5 == 0:
            split = "train"
        elif i % 5 in {1, 2}:
            split = "validation"
        else:
            split = "test"

        if disease in disease_to_drugs and all_drugs:
            good = disease_to_drugs[disease][0]
            bad_candidates = [x for x in all_drugs if x != good]
            bad = rng.choice(bad_candidates) if bad_candidates else good
            q = f"{disease}常用药物是什么？"
            out.append(
                {
                    "id": f"cm3kg_drug_{i:06d}_pos",
                    "query": q,
                    "answer": f"常用药物包括：{good}。",
                    "expected_risk": "low",
                    "meta": {"split": split, "source_dataset": "CM3KG", "type": "drug"},
                }
            )
            out.append(
                {
                    "id": f"cm3kg_drug_{i:06d}_neg",
                    "query": q,
                    "answer": f"常用药物包括：{bad}。",
                    "expected_risk": "high",
                    "meta": {
                        "split": split,
                        "source_dataset": "CM3KG",
                        "type": "drug",
                        "construction": "entity_replacement",
                    },
                }
            )
            continue

        if disease in disease_to_symptoms and all_symptoms:
            good = disease_to_symptoms[disease][0]
            bad_candidates = [x for x in all_symptoms if x != good]
            bad = rng.choice(bad_candidates) if bad_candidates else good
            q = f"{disease}常见症状是什么？"
            out.append(
                {
                    "id": f"cm3kg_sym_{i:06d}_pos",
                    "query": q,
                    "answer": f"常见症状包括：{good}。",
                    "expected_risk": "low",
                    "meta": {"split": split, "source_dataset": "CM3KG", "type": "symptom"},
                }
            )
            out.append(
                {
                    "id": f"cm3kg_sym_{i:06d}_neg",
                    "query": q,
                    "answer": f"常见症状包括：{bad}。",
                    "expected_risk": "high",
                    "meta": {
                        "split": split,
                        "source_dataset": "CM3KG",
                        "type": "symptom",
                        "construction": "entity_replacement",
                    },
                }
            )

    return out


def build_core_kb(med_df: pd.DataFrame, disease_df: pd.DataFrame, max_rows: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed + 17)
    rows: list[dict[str, Any]] = []

    for _, rec in med_df.iterrows():
        disease = str(rec.get("name", "") or "").strip()
        if not disease:
            continue
        dhead = f"{disease}[疾病]"

        for symptom in parse_list_field(rec.get("symptom"))[:12]:
            rows.append(
                {
                    "head": dhead,
                    "relation": "has_symptom",
                    "tail": symptom,
                    "text": f"{disease}的常见症状包括{symptom}",
                }
            )

        for check in parse_list_field(rec.get("check"))[:10]:
            rows.append(
                {
                    "head": dhead,
                    "relation": "requires_check",
                    "tail": check,
                    "text": f"{disease}常见检查包括{check}",
                }
            )

        drugs = list(
            dict.fromkeys(parse_list_field(rec.get("recommand_drug")) + parse_list_field(rec.get("common_drug")))
        )
        for drug in drugs[:12]:
            rows.append(
                {
                    "head": drug,
                    "relation": "treats",
                    "tail": disease,
                    "text": f"{drug}可用于治疗{disease}",
                }
            )

        for food in parse_list_field(rec.get("not_eat"))[:8]:
            rows.append(
                {
                    "head": dhead,
                    "relation": "contraindicated_for",
                    "tail": food,
                    "text": f"{disease}患者应避免食用{food}",
                }
            )

    # Add additional raw triples from Disease.csv with basic cleaning.
    for _, rec in disease_df.iterrows():
        h = str(rec.get("head", "") or "").strip()
        r = str(rec.get("relation", "") or "").strip()
        t = str(rec.get("tail", "") or "").strip()
        if not h or not r or not t:
            continue
        if len(r) > 30:  # filter broken noisy relation descriptions
            continue
        rows.append({"head": h, "relation": r, "tail": t, "text": f"{h}{r}{t}"})

    # Deduplicate triples and optionally downsample.
    dedup: list[dict[str, Any]] = []
    seen = set()
    for row in rows:
        key = (row["head"], row["relation"], row["tail"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)

    if max_rows > 0 and len(dedup) > max_rows:
        rng.shuffle(dedup)
        dedup = dedup[:max_rows]
    return dedup


def main() -> int:
    parser = argparse.ArgumentParser(description="Build real assets from CM3KG")
    parser.add_argument("--cm3kg-dir", default="CM3KG")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-sft-rows", type=int, default=60000)
    parser.add_argument("--max-benchmark-pairs", type=int, default=4000)
    parser.add_argument("--max-kb-rows", type=int, default=180000)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    cm3kg_dir = (root / args.cm3kg_dir).resolve()
    medical_csv = cm3kg_dir / "medical.csv"
    disease_csv = cm3kg_dir / "Disease.csv"
    if not medical_csv.exists() or not disease_csv.exists():
        raise FileNotFoundError(f"CM3KG files missing under {cm3kg_dir}")

    med_df = pd.read_csv(medical_csv)
    disease_df = pd.read_csv(disease_csv, names=["head", "relation", "tail"])

    sft_rows = build_sft_rows(med_df, max_rows=args.max_sft_rows, seed=args.seed)
    train, dev, test = split_rows(sft_rows, seed=args.seed)

    for split_name, split_data in [("train", train), ("dev", dev), ("test", test)]:
        for row in split_data:
            row.setdefault("meta", {})
            row["meta"]["split"] = split_name

    benchmark_rows = build_benchmark(med_df, max_pairs=args.max_benchmark_pairs, seed=args.seed)
    kb_rows = build_core_kb(med_df, disease_df, max_rows=args.max_kb_rows, seed=args.seed)

    train_path = root / "data/clean/real_sft_train.jsonl"
    dev_path = root / "data/clean/real_sft_dev.jsonl"
    test_path = root / "data/clean/real_sft_test.jsonl"
    benchmark_path = root / "data/benchmark/real_medqa_benchmark.jsonl"
    kb_path = root / "data/kg/cm3kg_core_kb.jsonl"

    write_jsonl(train_path, train)
    write_jsonl(dev_path, dev)
    write_jsonl(test_path, test)
    write_jsonl(benchmark_path, benchmark_rows)
    write_jsonl(kb_path, kb_rows)

    summary = {
        "source": {
            "dataset": "CM3KG (from CMKG project)",
            "cm3kg_dir": str(cm3kg_dir),
            "medical_csv_rows": int(len(med_df)),
            "disease_csv_rows": int(len(disease_df)),
            "license_notice": "Please verify CMKG upstream license terms before publication/distribution.",
        },
        "train_count": len(train),
        "dev_count": len(dev),
        "test_count": len(test),
        "benchmark_count": len(benchmark_rows),
        "kb_count": len(kb_rows),
        "seed": args.seed,
        "artifacts": {
            "train_file": str(train_path.relative_to(root)),
            "dev_file": str(dev_path.relative_to(root)),
            "test_file": str(test_path.relative_to(root)),
            "benchmark_file": str(benchmark_path.relative_to(root)),
            "kb_file": str(kb_path.relative_to(root)),
        },
        "sha256": {
            "train": file_sha256(train_path),
            "dev": file_sha256(dev_path),
            "test": file_sha256(test_path),
            "benchmark": file_sha256(benchmark_path),
            "kb": file_sha256(kb_path),
        },
    }

    summary_path = root / "reports/real_dataset_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        "# 真实数据集构建报告（CM3KG）",
        "",
        "- 数据来源：`CM3KG/medical.csv` + `CM3KG/Disease.csv`（本地真实知识图谱数据）",
        f"- 疾病条目数：{len(med_df)}",
        f"- 原始三元组数：{len(disease_df)}",
        "",
        "## 产出规模",
        f"- 训练集：{len(train)}",
        f"- 验证集：{len(dev)}",
        f"- 测试集：{len(test)}",
        f"- 幻觉评测基准（正/负）：{len(benchmark_rows)}",
        f"- 检索知识库条目：{len(kb_rows)}",
        "",
        "## 产物路径",
        f"- `{train_path.relative_to(root)}`",
        f"- `{dev_path.relative_to(root)}`",
        f"- `{test_path.relative_to(root)}`",
        f"- `{benchmark_path.relative_to(root)}`",
        f"- `{kb_path.relative_to(root)}`",
        "",
        "## 合规说明",
        "- CM3KG 来自公开仓库下载；发布论文前需再次核验上游许可条款与再分发限制。",
    ]
    (root / "reports/real_dataset_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
