#!/usr/bin/env python3
"""Build an integrated CMeKG-style JSONL from local CM3KG assets."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Any


LIST_SPLIT_RE = re.compile(r"[、,，;/；|]")
NAN_LIKE = {"", "nan", "none", "null", "[]"}


def norm_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in NAN_LIKE:
        return ""
    return re.sub(r"\s+", " ", text)


def unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def parse_list_field(value: Any) -> list[str]:
    text = norm_text(value)
    if not text:
        return []

    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                cleaned = [norm_text(x).strip("\"' ") for x in parsed]
                return [x for x in unique_keep_order(cleaned) if x]
        except Exception:
            pass

    stripped = text.strip("[]")
    parts = [norm_text(x).strip("\"' ") for x in LIST_SPLIT_RE.split(stripped)]
    return [x for x in unique_keep_order(parts) if x]


def iter_medical_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        pd = None

    if pd is not None:
        frame = pd.read_csv(path, dtype=str)
        return [dict(row) for row in frame.to_dict(orient="records")]

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def load_alias_pickle(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        obj = pickle.load(f)
    if not isinstance(obj, dict):
        return {}

    out: dict[str, list[str]] = {}
    for key, val in obj.items():
        entity = norm_text(key)
        if not entity:
            continue
        if isinstance(val, list):
            aliases = [norm_text(x).strip("\"' ") for x in val]
            aliases = [x for x in unique_keep_order(aliases) if x and x != entity]
            if aliases:
                out[entity] = aliases
    return out


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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


def build_kg(
    cm3kg_dir: Path,
    merge_demo: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    medical_csv = cm3kg_dir / "medical.csv"
    if not medical_csv.exists():
        raise FileNotFoundError(f"missing required file: {medical_csv}")

    triples: list[dict[str, Any]] = []
    triple_keys: set[tuple[str, str, str]] = set()
    relation_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()

    def add_triple(
        head: str,
        relation: str,
        tail: str,
        head_type: str,
        tail_type: str,
        source: str,
    ) -> None:
        h = norm_text(head)
        r = norm_text(relation)
        t = norm_text(tail)
        if not h or not r or not t:
            return
        key = (h, r, t)
        if key in triple_keys:
            return
        triple_keys.add(key)
        triples.append(
            {
                "head": h,
                "head_type": head_type,
                "relation": r,
                "tail": t,
                "tail_type": tail_type,
                "source": source,
            }
        )
        relation_counter[r] += 1
        source_counter[source] += 1

    medical_rows = iter_medical_rows(medical_csv)
    for row in medical_rows:
        disease = norm_text(row.get("name"))
        if not disease:
            continue

        symptoms = parse_list_field(row.get("symptom"))
        recommended = parse_list_field(row.get("recommand_drug"))
        common_drugs = parse_list_field(row.get("common_drug"))
        checks = parse_list_field(row.get("check"))
        acompanies = parse_list_field(row.get("acompany"))
        do_eat = parse_list_field(row.get("do_eat"))
        not_eat = parse_list_field(row.get("not_eat"))

        for symptom in symptoms[:40]:
            add_triple(disease, "has_symptom", symptom, "disease", "symptom", "CM3KG.medical")
        for check_item in checks[:20]:
            add_triple(
                disease,
                "requires_check",
                check_item,
                "disease",
                "medical_test",
                "CM3KG.medical",
            )
        for acomp in acompanies[:20]:
            add_triple(disease, "comorbidity", acomp, "disease", "disease", "CM3KG.medical")

        all_drugs = unique_keep_order(common_drugs + recommended)
        for drug in all_drugs[:40]:
            add_triple(disease, "recommended_drug", drug, "disease", "drug", "CM3KG.medical")
            add_triple(drug, "treats", disease, "drug", "disease", "CM3KG.medical")

        for food in do_eat[:20]:
            add_triple(
                disease,
                "diet_recommendation",
                food,
                "disease",
                "food",
                "CM3KG.medical",
            )
        for food in not_eat[:20]:
            add_triple(disease, "diet_avoid", food, "disease", "food", "CM3KG.medical")

    disease_aliases = load_alias_pickle(cm3kg_dir / "diseases.pk")
    symptom_aliases = load_alias_pickle(cm3kg_dir / "symptoms.pk")
    for disease, aliases in disease_aliases.items():
        for alias in aliases[:30]:
            add_triple(alias, "alias_of", disease, "disease_alias", "disease", "CM3KG.alias")
    for symptom, aliases in symptom_aliases.items():
        for alias in aliases[:30]:
            add_triple(alias, "alias_of", symptom, "symptom_alias", "symptom", "CM3KG.alias")

    merged_demo = 0
    if merge_demo is not None and merge_demo.exists():
        for row in load_jsonl(merge_demo):
            add_triple(
                str(row.get("head", "")),
                str(row.get("relation", "")),
                str(row.get("tail", "")),
                str(row.get("head_type", "") or "entity"),
                str(row.get("tail_type", "") or "entity"),
                str(row.get("source", "") or "cmekg_demo"),
            )
            merged_demo += 1

    summary = {
        "medical_rows": len(medical_rows),
        "disease_alias_entities": len(disease_aliases),
        "symptom_alias_entities": len(symptom_aliases),
        "merged_demo_rows": merged_demo,
        "triple_count": len(triples),
        "relation_counter": dict(relation_counter),
        "source_counter": dict(source_counter),
    }
    return triples, summary


def write_report(path: Path, summary: dict[str, Any], output: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rel_items = sorted(summary["relation_counter"].items(), key=lambda x: x[1], reverse=True)
    src_items = sorted(summary["source_counter"].items(), key=lambda x: x[1], reverse=True)

    lines = [
        "# CM3KG -> CMeKG 集成构建报告",
        "",
        "## 输入统计",
        f"- medical.csv 行数: {summary['medical_rows']}",
        f"- disease alias 实体数: {summary['disease_alias_entities']}",
        f"- symptom alias 实体数: {summary['symptom_alias_entities']}",
        f"- 额外合并 demo 三元组行数: {summary['merged_demo_rows']}",
        "",
        "## 输出统计",
        f"- 三元组总数: {summary['triple_count']}",
        f"- 输出文件: `{output}`",
        "",
        "## 关系分布",
        "| relation | count |",
        "|---|---:|",
    ]
    for rel, count in rel_items:
        lines.append(f"| {rel} | {count} |")

    lines.extend(
        [
            "",
            "## 来源分布",
            "| source | count |",
            "|---|---:|",
        ]
    )
    for src, count in src_items:
        lines.append(f"| {src} | {count} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build integrated KG from CM3KG files")
    parser.add_argument("--cm3kg-dir", default="CM3KG", help="CM3KG data directory")
    parser.add_argument("--output", default="data/kg/cmekg_integrated.jsonl", help="Output KG jsonl")
    parser.add_argument("--report", default="reports/cm3kg_kg_report.md", help="Output report markdown")
    parser.add_argument("--summary-json", default="reports/cm3kg_kg_summary.json", help="Output summary json")
    parser.add_argument(
        "--merge-demo",
        default="data/kg/cmekg_demo.jsonl",
        help="Optional extra KG to merge for guardrail relations",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    cm3kg_dir = (root / args.cm3kg_dir).resolve()
    output_path = (root / args.output).resolve()
    report_path = (root / args.report).resolve()
    summary_path = (root / args.summary_json).resolve()
    merge_demo = (root / args.merge_demo).resolve() if args.merge_demo else None

    triples, summary = build_kg(cm3kg_dir=cm3kg_dir, merge_demo=merge_demo)
    save_jsonl(output_path, triples)
    write_report(report_path, summary, output_path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"output": str(output_path), **summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
