#!/usr/bin/env python3
"""Analyze rule-only vs hybrid(LLM fallback) detection impact from prediction artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


POSITIVE_LEVELS = {"high", "medium"}


@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.tn + self.fn


@dataclass
class MetricPack:
    accuracy: float
    precision: float
    recall: float
    f1: float
    specificity: float
    fpr: float
    fnr: float


def is_positive(risk: str) -> bool:
    return str(risk).strip().lower() in POSITIVE_LEVELS


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_split_spec(spec: str) -> set[str]:
    return {x.strip().lower() for x in (spec or "").split(",") if x.strip()}


def confusion(rows: list[dict[str, Any]], key: str) -> Confusion:
    c = Confusion()
    for row in rows:
        gold_pos = is_positive(str(row.get("expected_risk", "low")))
        pred_pos = is_positive(str(row.get(key, "low")))
        if gold_pos and pred_pos:
            c.tp += 1
        elif (not gold_pos) and pred_pos:
            c.fp += 1
        elif (not gold_pos) and (not pred_pos):
            c.tn += 1
        else:
            c.fn += 1
    return c


def metrics(c: Confusion) -> MetricPack:
    precision = c.tp / (c.tp + c.fp) if (c.tp + c.fp) else 0.0
    recall = c.tp / (c.tp + c.fn) if (c.tp + c.fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (c.tp + c.tn) / max(c.total, 1)
    specificity = c.tn / (c.tn + c.fp) if (c.tn + c.fp) else 0.0
    fpr = c.fp / (c.fp + c.tn) if (c.fp + c.tn) else 0.0
    fnr = c.fn / (c.fn + c.tp) if (c.fn + c.tp) else 0.0
    return MetricPack(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        specificity=specificity,
        fpr=fpr,
        fnr=fnr,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "variant",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "specificity",
        "fpr",
        "fnr",
        "tp",
        "fp",
        "tn",
        "fn",
        "sample_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze LLM fallback impact")
    parser.add_argument("--predictions", default="reports/detection_predictions_v2_hybrid_llm.jsonl")
    parser.add_argument("--report", default="reports/detection_eval_v2_hybrid_llm_impact.md")
    parser.add_argument("--csv", default="reports/thesis_assets/tables/detection_v2_hybrid_llm_impact.csv")
    parser.add_argument("--json", default="reports/thesis_support/detection_v2_hybrid_llm_impact.json")
    parser.add_argument("--include-splits", default="")
    parser.add_argument("--max-samples", type=int, default=0)
    args = parser.parse_args()

    pred_path = Path(args.predictions)
    if not pred_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {pred_path}")

    rows = load_jsonl(pred_path)
    include_splits = parse_split_spec(args.include_splits)
    split_filter_applied = False
    if include_splits:
        filtered = [r for r in rows if str(r.get("split", "")).strip().lower() in include_splits]
        if filtered:
            rows = filtered
            split_filter_applied = True
        elif all("split" not in r for r in rows):
            split_filter_applied = False
        else:
            rows = filtered
            split_filter_applied = True
    if args.max_samples > 0 and len(rows) > args.max_samples:
        rows = rows[: args.max_samples]

    if not rows:
        raise ValueError("No rows available after filtering")

    for row in rows:
        if "base_predicted_risk" not in row:
            row["base_predicted_risk"] = row.get("predicted_risk", "low")

    c_base = confusion(rows, key="base_predicted_risk")
    c_hybrid = confusion(rows, key="predicted_risk")
    m_base = metrics(c_base)
    m_hybrid = metrics(c_hybrid)

    llm_used = sum(1 for r in rows if bool(r.get("llm_used", False)))
    llm_promoted = sum(
        1
        for r in rows
        if bool(r.get("llm_promoted", False))
        or str(r.get("base_predicted_risk", "")) != str(r.get("predicted_risk", ""))
    )

    def row_for(name: str, m: MetricPack, c: Confusion) -> dict[str, Any]:
        return {
            "variant": name,
            "accuracy": round(m.accuracy, 6),
            "precision": round(m.precision, 6),
            "recall": round(m.recall, 6),
            "f1": round(m.f1, 6),
            "specificity": round(m.specificity, 6),
            "fpr": round(m.fpr, 6),
            "fnr": round(m.fnr, 6),
            "tp": c.tp,
            "fp": c.fp,
            "tn": c.tn,
            "fn": c.fn,
            "sample_count": c.total,
        }

    csv_rows = [
        row_for("rule_only", m_base, c_base),
        row_for("hybrid_with_llm", m_hybrid, c_hybrid),
        {
            "variant": "delta(hybrid-rule)",
            "accuracy": round(m_hybrid.accuracy - m_base.accuracy, 6),
            "precision": round(m_hybrid.precision - m_base.precision, 6),
            "recall": round(m_hybrid.recall - m_base.recall, 6),
            "f1": round(m_hybrid.f1 - m_base.f1, 6),
            "specificity": round(m_hybrid.specificity - m_base.specificity, 6),
            "fpr": round(m_hybrid.fpr - m_base.fpr, 6),
            "fnr": round(m_hybrid.fnr - m_base.fnr, 6),
            "tp": c_hybrid.tp - c_base.tp,
            "fp": c_hybrid.fp - c_base.fp,
            "tn": c_hybrid.tn - c_base.tn,
            "fn": c_hybrid.fn - c_base.fn,
            "sample_count": c_hybrid.total,
        },
    ]
    write_csv(Path(args.csv), csv_rows)

    report_lines = [
        "# v2 Hybrid LLM Fallback Impact",
        "",
        f"- predictions: `{pred_path}`",
        f"- samples: {len(rows)}",
        f"- split filter: `{args.include_splits or 'ALL'}` "
        f"(applied={split_filter_applied if include_splits else False})",
        f"- llm_used: {llm_used}",
        f"- llm_promotions: {llm_promoted}",
        "",
        "| variant | accuracy | precision | recall | f1 | specificity | fpr | fnr | tp | fp | tn | fn |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in csv_rows:
        report_lines.append(
            "| {variant} | {accuracy:.4f} | {precision:.4f} | {recall:.4f} | {f1:.4f} | {specificity:.4f} | "
            "{fpr:.4f} | {fnr:.4f} | {tp} | {fp} | {tn} | {fn} |".format(
                variant=row["variant"],
                accuracy=float(row["accuracy"]),
                precision=float(row["precision"]),
                recall=float(row["recall"]),
                f1=float(row["f1"]),
                specificity=float(row["specificity"]),
                fpr=float(row["fpr"]),
                fnr=float(row["fnr"]),
                tp=row["tp"],
                fp=row["fp"],
                tn=row["tn"],
                fn=row["fn"],
            )
        )

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    summary = {
        "samples": len(rows),
        "llm_used": llm_used,
        "llm_promotions": llm_promoted,
        "rule_only": row_for("rule_only", m_base, c_base),
        "hybrid": row_for("hybrid_with_llm", m_hybrid, c_hybrid),
        "delta": {
            "accuracy": m_hybrid.accuracy - m_base.accuracy,
            "precision": m_hybrid.precision - m_base.precision,
            "recall": m_hybrid.recall - m_base.recall,
            "f1": m_hybrid.f1 - m_base.f1,
            "specificity": m_hybrid.specificity - m_base.specificity,
            "fpr": m_hybrid.fpr - m_base.fpr,
            "fnr": m_hybrid.fnr - m_base.fnr,
        },
    }
    json_path = Path(args.json)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"samples": len(rows), "llm_used": llm_used, "report": str(report_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
