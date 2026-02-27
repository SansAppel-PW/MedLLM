#!/usr/bin/env python3
"""End-to-end data governance pipeline for MedLLM (T104-T110)."""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print("[run]", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_default_kg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
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


def ensure_reference_kg(repo_root: Path, kg_path: Path, cm3kg_dir: Path) -> None:
    if kg_path.exists():
        return

    cm3kg_medical = cm3kg_dir / "medical.csv"
    if cm3kg_medical.exists():
        run_cmd(
            [
                sys.executable,
                "scripts/data/build_cmekg_from_cm3kg.py",
                "--cm3kg-dir",
                str(cm3kg_dir.relative_to(repo_root)),
                "--output",
                str(kg_path.relative_to(repo_root)),
                "--report",
                "reports/cm3kg_kg_report.md",
                "--summary-json",
                "reports/cm3kg_kg_summary.json",
                "--merge-demo",
                "data/kg/cmekg_demo.jsonl",
            ],
            cwd=repo_root,
        )
        return

    # Fallback for environments without CM3KG assets.
    build_default_kg(kg_path)


def split_train_dev(rows: list[dict[str, Any]], dev_ratio: float, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    copied = list(rows)
    rng.shuffle(copied)
    dev_size = max(1, int(len(copied) * dev_ratio)) if copied else 0
    dev = copied[:dev_size]
    train = copied[dev_size:]
    if not train and dev:
        train = dev[:]
    return train, dev


def perturb_answer(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        return "请直接使用未核实处方。"

    # Prefer numeric perturbation for hard negatives.
    m = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|ml)", text, flags=re.IGNORECASE)
    if m:
        original = float(m.group(1))
        unit = m.group(2)
        wrong = original * 10
        wrong_str = f"{wrong:.0f}" if wrong.is_integer() else f"{wrong:.2f}"
        return text[: m.start()] + f"{wrong_str}{unit}" + text[m.end() :]

    # Semantic inversion fallback.
    replacements = [
        ("不建议", "建议"),
        ("避免", "优先"),
        ("禁忌", "适用"),
        ("需要医生", "无需医生"),
    ]
    for src, dst in replacements:
        if src in text:
            return text.replace(src, dst, 1)

    return text + " 建议忽略禁忌症并立即自行用药。"


def build_preference_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for row in rows:
        prompt = str(row.get("query", ""))
        context = str(row.get("context", ""))
        if context:
            prompt = f"{prompt}\n\n上下文:\n{context}"
        chosen = str(row.get("answer", ""))
        rejected = perturb_answer(chosen)
        pairs.append(
            {
                "id": row.get("id"),
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "meta": {
                    "source": row.get("meta", {}).get("dataset", "unknown"),
                    "conflict_level": row.get("meta", {}).get("conflict_level", "none"),
                    "construction": "rule_based_hard_negative",
                },
            }
        )
    return pairs


def write_report(
    path: Path,
    stats: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = [
        "# 数据清洗质量报告",
        "",
        "## 概览",
        f"- 原始样本数: {stats['raw_count']}",
        f"- Schema有效样本数: {stats['normalized_count']}",
        f"- 清洗后保留样本数: {stats['clean_count']}",
        f"- 删除样本数: {stats['dropped_count']}",
        f"- 重写样本数: {stats['rewritten_count']}",
        "",
        "## 三元组与冲突",
        f"- 候选三元组数: {stats['candidate_triples']}",
        f"- 冲突三元组数: {stats['conflict_triples']}",
        f"- 高风险冲突数: {stats['high_conflicts']}",
        "",
        "## 产物路径",
        f"- SFT 训练集: `{stats['sft_train_path']}`",
        f"- SFT 验证集: `{stats['sft_dev_path']}`",
        f"- 偏好对数据: `{stats['pref_pairs_path']}`",
        f"- 重写审计日志: `{stats['rewrite_log_path']}`",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run data governance pipeline")
    parser.add_argument("--input", default="data/raw/schema_examples.json", help="Raw input file")
    parser.add_argument("--kg", default="data/kg/cmekg_integrated.jsonl", help="Reference KG file")
    parser.add_argument("--cm3kg-dir", default="CM3KG", help="CM3KG data directory")
    parser.add_argument("--dataset", default="med_demo", help="Dataset name tag")
    parser.add_argument("--split", default="train", help="Split tag")
    parser.add_argument("--dev-ratio", type=float, default=0.2, help="Dev set ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]

    input_path = (repo_root / args.input).resolve()
    kg_path = (repo_root / args.kg).resolve()
    cm3kg_dir = (repo_root / args.cm3kg_dir).resolve()
    ensure_reference_kg(repo_root=repo_root, kg_path=kg_path, cm3kg_dir=cm3kg_dir)

    normalized = repo_root / "data/raw/normalized_records.jsonl"
    pii_cleaned = repo_root / "data/raw/normalized_records_pii.jsonl"
    entities_out = repo_root / "data/kg/entities.jsonl"
    candidate_triples = repo_root / "data/kg/triples/candidate_triples.jsonl"
    validated_triples = repo_root / "data/kg/triples/validated_triples.jsonl"
    record_summary = repo_root / "data/kg/triples/record_conflicts.jsonl"
    cleaned_all = repo_root / "data/clean/sft_all.jsonl"
    rewrite_log = repo_root / "data/clean/rewrite_audit.jsonl"
    sft_train = repo_root / "data/clean/sft_train.jsonl"
    sft_dev = repo_root / "data/clean/sft_dev.jsonl"
    pref_pairs = repo_root / "data/clean/pref_seed_pairs.jsonl"
    report_path = repo_root / "reports/data_cleaning_report.md"

    run_cmd(
        [
            sys.executable,
            "-m",
            "src.data.schema",
            "--input",
            str(input_path),
            "--output",
            str(normalized),
            "--dataset",
            args.dataset,
            "--split",
            args.split,
        ],
        cwd=repo_root,
    )

    run_cmd(
        [
            sys.executable,
            "-m",
            "src.data.pii_cleaner",
            "--input",
            str(normalized),
            "--output",
            str(pii_cleaned),
            "--fields",
            "query,context,answer,meta.contact",
            "--report",
            str(repo_root / "reports/pii_cleaning_report.json"),
        ],
        cwd=repo_root,
    )

    run_cmd(
        [
            sys.executable,
            "-m",
            "src.data.ner_el_pipeline",
            "--input",
            str(pii_cleaned),
            "--kg",
            str(kg_path),
            "--output",
            str(entities_out),
        ],
        cwd=repo_root,
    )

    run_cmd(
        [
            sys.executable,
            "-m",
            "src.data.triple_mapper",
            "--input",
            str(pii_cleaned),
            "--entities",
            str(entities_out),
            "--output",
            str(candidate_triples),
        ],
        cwd=repo_root,
    )

    run_cmd(
        [
            sys.executable,
            "-m",
            "src.data.kg_validator",
            "--input",
            str(candidate_triples),
            "--kg",
            str(kg_path),
            "--output",
            str(validated_triples),
            "--record-summary-output",
            str(record_summary),
        ],
        cwd=repo_root,
    )

    run_cmd(
        [
            sys.executable,
            "-m",
            "src.data.rewrite_low_conflict",
            "--input",
            str(pii_cleaned),
            "--validated",
            str(validated_triples),
            "--output",
            str(cleaned_all),
            "--rewrite-log",
            str(rewrite_log),
        ],
        cwd=repo_root,
    )

    cleaned_rows = load_jsonl(cleaned_all)
    train_rows, dev_rows = split_train_dev(cleaned_rows, args.dev_ratio, args.seed)
    save_jsonl(sft_train, train_rows)
    save_jsonl(sft_dev, dev_rows)

    pref_rows = build_preference_pairs(cleaned_rows)
    save_jsonl(pref_pairs, pref_rows)

    raw_rows = load_jsonl(normalized)
    rewrite_rows = load_jsonl(rewrite_log)
    valid_triples = load_jsonl(validated_triples)

    stats = {
        "raw_count": len(raw_rows),
        "normalized_count": len(raw_rows),
        "clean_count": len(cleaned_rows),
        "dropped_count": sum(1 for x in rewrite_rows if x.get("action") == "drop"),
        "rewritten_count": sum(1 for x in rewrite_rows if x.get("action") == "rewrite"),
        "candidate_triples": len(load_jsonl(candidate_triples)),
        "conflict_triples": sum(1 for x in valid_triples if x.get("validation_status") == "conflict"),
        "high_conflicts": sum(1 for x in valid_triples if x.get("conflict_level") == "high"),
        "sft_train_path": str(sft_train.relative_to(repo_root)),
        "sft_dev_path": str(sft_dev.relative_to(repo_root)),
        "pref_pairs_path": str(pref_pairs.relative_to(repo_root)),
        "rewrite_log_path": str(rewrite_log.relative_to(repo_root)),
    }

    write_report(report_path, stats)
    print("[pipeline] done")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
