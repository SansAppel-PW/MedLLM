#!/usr/bin/env python3
"""Heuristic NLI checker for fact-evidence consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .common import jaccard_similarity, tokenize
except ImportError:  # pragma: no cover
    from common import jaccard_similarity, tokenize


NEG_CUES = ["禁忌", "禁用", "避免", "不宜", "不可"]
POS_CUES = ["治疗", "可用于", "适用", "推荐", "首选"]


def cue_polarity(text: str) -> str:
    has_neg = any(k in text for k in NEG_CUES)
    has_pos = any(k in text for k in POS_CUES)
    if has_neg and not has_pos:
        return "neg"
    if has_pos and not has_neg:
        return "pos"
    return "mix"


def classify_fact_with_doc(fact: str, doc_text: str, base_score: float) -> tuple[str, float]:
    fact_tokens = tokenize(fact)
    doc_tokens = tokenize(doc_text)
    overlap = jaccard_similarity(fact_tokens, doc_tokens)

    if overlap < 0.08 and base_score < 0.15:
        return "neutral", 0.2

    fact_pol = cue_polarity(fact)
    doc_pol = cue_polarity(doc_text)

    if fact_pol != "mix" and doc_pol != "mix" and fact_pol != doc_pol:
        return "contradict", min(1.0, 0.6 + overlap)

    if overlap > 0.22:
        return "entail", min(1.0, 0.5 + overlap)

    return "neutral", max(0.2, overlap)


def classify_fact(fact: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    best_entail = ("neutral", 0.0, None)
    best_contra = ("neutral", 0.0, None)

    for doc in docs:
        label, conf = classify_fact_with_doc(fact, str(doc.get("text", "")), float(doc.get("score", 0.0)))
        item = {"doc_id": doc.get("doc_id"), "text": doc.get("text"), "score": doc.get("score")}
        if label == "entail" and conf > best_entail[1]:
            best_entail = (label, conf, item)
        if label == "contradict" and conf > best_contra[1]:
            best_contra = (label, conf, item)

    if best_contra[1] >= 0.6:
        return {
            "fact": fact,
            "label": "contradict",
            "confidence": round(best_contra[1], 6),
            "evidence": best_contra[2],
        }

    if best_entail[1] >= 0.55:
        return {
            "fact": fact,
            "label": "entail",
            "confidence": round(best_entail[1], 6),
            "evidence": best_entail[2],
        }

    return {"fact": fact, "label": "neutral", "confidence": 0.3, "evidence": None}


def run_batch(evidence_path: Path, output_path: Path) -> None:
    rows = []
    with evidence_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    out = []
    for row in rows:
        rid = row.get("id")
        evidence = row.get("evidence", [])
        fact_results = []
        for item in evidence:
            fact = str(item.get("fact", ""))
            top_docs = list(item.get("top_docs", []))
            fact_results.append(classify_fact(fact, top_docs))
        out.append({"id": rid, "fact_results": fact_results})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[nli] input={len(rows)} output={len(out)} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Heuristic NLI checker")
    parser.add_argument("--evidence", required=True, help="Evidence jsonl from retriever")
    parser.add_argument("--output", required=True, help="Output jsonl")
    args = parser.parse_args()

    run_batch(Path(args.evidence), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
