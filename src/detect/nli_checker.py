#!/usr/bin/env python3
"""Heuristic NLI checker for fact-evidence consistency."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from .common import jaccard_similarity, tokenize
except ImportError:  # pragma: no cover
    from common import jaccard_similarity, tokenize


NEG_CUES = [
    "禁忌",
    "禁用",
    "避免",
    "不宜",
    "不可",
    "不应",
    "禁止",
    "contraindicated",
    "avoid",
    "not recommended",
    "should not",
    "must not",
    "unsafe",
]
POS_CUES = [
    "治疗",
    "可用于",
    "适用",
    "推荐",
    "优先",
    "首选",
    "可以",
    "可用",
    "可使用",
    "适合",
    "recommended",
    "indicated",
    "can use",
    "safe",
    "first line",
]

ANSWER_PREFIX_RE = re.compile(r"(?:正确答案|correct answer)\s*[:：]?\s*", flags=re.IGNORECASE)
DOSAGE_VALUE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:mg|毫克)", flags=re.IGNORECASE)
DOSAGE_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:\.\d+)?)")


def extract_answer_signal(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    lowered = raw.lower()
    has_prefix = bool(re.search(r"(正确答案|correct answer)", raw, flags=re.IGNORECASE))

    letter = None
    m = re.search(r"(?:正确答案|correct answer)\s*[:：]?\s*([A-D])(?:[.\)\s]|$)", raw, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"\b([A-D])(?:[.\)\s]|$)", raw, flags=re.IGNORECASE)
    if m:
        letter = m.group(1).upper()

    payload = ANSWER_PREFIX_RE.sub("", raw)
    payload = re.sub(r"^[A-D](?:[.\)\s]+)", "", payload, flags=re.IGNORECASE)
    payload = re.sub(r"\s+", " ", payload).strip().strip(".,:; ")

    return {
        "has_prefix": has_prefix,
        "letter": letter,
        "payload": payload.lower(),
        "raw": lowered,
    }


def cue_polarity(text: str) -> str:
    lowered = (text or "").lower()
    has_neg = any(k in lowered for k in NEG_CUES)
    has_pos = any(k in lowered for k in POS_CUES)
    if has_neg and not has_pos:
        return "neg"
    if has_pos and not has_neg:
        return "pos"
    return "mix"


def extract_dosage_values(text: str) -> list[float]:
    values = []
    for item in DOSAGE_VALUE_RE.findall(text or ""):
        try:
            values.append(float(item))
        except ValueError:
            continue
    return values


def extract_dosage_range(text: str) -> tuple[float, float] | None:
    raw = text or ""
    for low, high in DOSAGE_RANGE_RE.findall(raw):
        try:
            lo = float(low)
            hi = float(high)
        except ValueError:
            continue
        if lo > hi:
            lo, hi = hi, lo
        return lo, hi

    values = extract_dosage_values(raw)
    if len(values) >= 2:
        lo = min(values)
        hi = max(values)
        return lo, hi
    return None


def compare_dosage_signals(fact: str, doc_text: str, relation: str) -> tuple[str, float] | None:
    rel = (relation or "").strip().lower()
    fact_values = extract_dosage_values(fact)
    if not fact_values:
        return None

    dose_range = extract_dosage_range(doc_text)
    if dose_range is None:
        return None

    # Prefer dosage checks for explicit dosage relations or dosage-like evidence text.
    if rel not in {"dosage", "dosage_range_mg"} and "剂量" not in (doc_text or "").lower():
        return None

    lo, hi = dose_range
    candidate = max(fact_values)
    if candidate < lo * 0.7 or candidate > hi * 1.3:
        return "contradict", 0.96
    if lo <= candidate <= hi:
        return "entail", 0.9
    return None


def compare_answer_signals(fact: str, doc_text: str) -> tuple[str, float] | None:
    fact_sig = extract_answer_signal(fact)
    doc_sig = extract_answer_signal(doc_text)

    if not (fact_sig["has_prefix"] and doc_sig["has_prefix"]):
        return None

    fact_letter = fact_sig["letter"]
    doc_letter = doc_sig["letter"]
    if fact_letter and doc_letter:
        if fact_letter == doc_letter:
            return "entail", 0.96
        return "contradict", 0.98

    fact_payload = str(fact_sig["payload"])
    doc_payload = str(doc_sig["payload"])
    if fact_payload and doc_payload:
        if fact_payload == doc_payload:
            return "entail", 0.94

        overlap = jaccard_similarity(tokenize(fact_payload), tokenize(doc_payload))
        if overlap < 0.35:
            return "contradict", min(0.95, 0.78 + (0.35 - overlap))
        if overlap >= 0.78:
            return "entail", min(0.92, 0.72 + overlap * 0.2)

    return None


def classify_fact_with_doc(
    fact: str,
    doc_text: str,
    base_score: float,
    relation: str = "",
) -> tuple[str, float]:
    fact_tokens = tokenize(fact)
    doc_tokens = tokenize(doc_text)
    overlap = jaccard_similarity(fact_tokens, doc_tokens)

    dosage_cmp = compare_dosage_signals(fact, doc_text, relation)
    if dosage_cmp is not None and (base_score >= 0.1 or relation in {"dosage", "dosage_range_mg"}):
        return dosage_cmp

    if base_score >= 0.18 or overlap >= 0.18:
        answer_cmp = compare_answer_signals(fact, doc_text)
        if answer_cmp is not None:
            return answer_cmp

    if overlap < 0.06 and base_score < 0.12:
        return "neutral", 0.2

    fact_pol = cue_polarity(fact)
    doc_pol = cue_polarity(doc_text)

    if fact_pol != "mix" and doc_pol != "mix" and fact_pol != doc_pol:
        return "contradict", min(1.0, 0.82 + 0.12 * overlap)

    if overlap > 0.2:
        return "entail", min(1.0, 0.5 + overlap)

    return "neutral", max(0.2, overlap)


def classify_fact(fact: str, docs: list[dict[str, Any]]) -> dict[str, Any]:
    best_entail = ("neutral", 0.0, 0.0, None)
    best_contra = ("neutral", 0.0, 0.0, None)

    for doc in docs:
        doc_score = float(doc.get("score", 0.0))
        relation = str(doc.get("relation", "") or "")
        label, conf = classify_fact_with_doc(fact, str(doc.get("text", "")), doc_score, relation=relation)
        if label == "contradict":
            weighted = conf * (0.55 + 0.45 * min(doc_score, 1.0))
        else:
            weighted = conf * (0.4 + 0.6 * min(doc_score, 1.0))
        item = {"doc_id": doc.get("doc_id"), "text": doc.get("text"), "score": doc.get("score")}
        if label == "entail" and weighted > best_entail[2]:
            best_entail = (label, conf, weighted, item)
        if label == "contradict" and weighted > best_contra[2]:
            best_contra = (label, conf, weighted, item)

    # Prefer strong entailment with clearly better evidence relevance.
    if best_entail[2] >= 0.70 and best_entail[2] >= best_contra[2] + 0.10:
        return {
            "fact": fact,
            "label": "entail",
            "confidence": round(best_entail[1], 6),
            "evidence": best_entail[3],
        }

    if best_contra[2] >= 0.35:
        return {
            "fact": fact,
            "label": "contradict",
            "confidence": round(best_contra[1], 6),
            "evidence": best_contra[3],
        }

    if best_entail[2] >= 0.45:
        return {
            "fact": fact,
            "label": "entail",
            "confidence": round(best_entail[1], 6),
            "evidence": best_entail[3],
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
