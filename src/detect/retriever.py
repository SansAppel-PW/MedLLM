#!/usr/bin/env python3
"""Lightweight lexical retrieval over KG / reference docs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from .common import jaccard_similarity, tokenize
except ImportError:  # pragma: no cover
    from common import jaccard_similarity, tokenize


RELATION_TEXT = {
    "treats": "可用于治疗",
    "contraindicated_for": "禁用于",
    "dosage_range_mg": "推荐剂量范围",
    "dosage": "用量",
    "reference_answer": "参考答案",
}


def stable_query_hash(text: str) -> str:
    norm = (text or "").strip().lower()
    return hashlib.md5(norm.encode("utf-8")).hexdigest()


def load_knowledge_docs(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    docs = []
    for i, row in enumerate(rows):
        h = str(row.get("head", ""))
        r = str(row.get("relation", ""))
        t = str(row.get("tail", ""))
        if row.get("text"):
            text = str(row.get("text", "")).strip()
        else:
            rel_text = RELATION_TEXT.get(r, r)
            text = f"{h}{rel_text}{t}" if h and t else str(row)
        if not text:
            continue
        docs.append(
            {
                "doc_id": f"kg_{i}",
                "text": text,
                "head": h,
                "relation": r,
                "tail": t,
                "query_hash": str(row.get("query_hash", "")) or (stable_query_hash(h) if h else ""),
                "tokens": tokenize(text),
            }
        )
    return docs


def score_doc(
    query_tokens: list[str],
    query_norm: str,
    doc: dict[str, Any],
    context_hash: str = "",
) -> float:
    if not query_tokens:
        return 0.0
    base = jaccard_similarity(query_tokens, doc.get("tokens", []))
    bonus = 0.0
    head = str(doc.get("head", "")).lower()
    tail = str(doc.get("tail", "")).lower()
    if head and head in query_norm:
        bonus += 0.25
    if tail and tail in query_norm:
        bonus += 0.15
    if context_hash and str(doc.get("query_hash", "")) == context_hash:
        bonus += 1.2
    return base + bonus


def retrieve(
    query: str,
    docs: list[dict[str, Any]],
    top_k: int = 5,
    min_score: float = 0.08,
    context_query: str = "",
) -> list[dict[str, Any]]:
    merged_query = f"{context_query}\n{query}" if context_query else query
    q_tokens = tokenize(merged_query)
    if not q_tokens:
        return []
    q_norm = (merged_query or "").lower()
    context_hash = stable_query_hash(context_query) if context_query else ""

    scored = []
    for doc in docs:
        s = score_doc(q_tokens, q_norm, doc, context_hash=context_hash)
        query_hash_match = bool(context_hash and str(doc.get("query_hash", "")) == context_hash)

        # Reference-answer docs are only reliable under exact query-hash match.
        # Otherwise keep a heavily down-weighted fallback score.
        if str(doc.get("relation", "")) == "reference_answer" and context_hash and not query_hash_match:
            s *= 0.22

        if s >= min_score:
            scored.append(
                {
                    "doc_id": doc["doc_id"],
                    "text": doc["text"],
                    "score": round(s, 6),
                    "head": doc.get("head"),
                    "relation": doc.get("relation"),
                    "tail": doc.get("tail"),
                    "query_hash_match": query_hash_match,
                }
            )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def run_batch(facts_path: Path, output_path: Path, kb_path: Path, top_k: int) -> None:
    docs = load_knowledge_docs(kb_path)
    rows = []
    with facts_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    out = []
    for row in rows:
        rid = row.get("id")
        facts = row.get("facts", [])
        fact_evidence = []
        for fact in facts:
            fact_evidence.append(
                {
                    "fact": fact,
                    "top_docs": retrieve(str(fact), docs, top_k=top_k),
                }
            )
        out.append({"id": rid, "evidence": fact_evidence})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[retriever] input={len(rows)} output={len(out)} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="KG retrieval module")
    parser.add_argument("--kb", default="data/kg/cmekg_demo.jsonl", help="Knowledge base jsonl")
    parser.add_argument("--query", default="", help="Single query")
    parser.add_argument("--facts", default="", help="Facts jsonl input")
    parser.add_argument("--output", default="", help="Batch output jsonl")
    parser.add_argument("--top-k", type=int, default=5, help="Top-k docs")
    args = parser.parse_args()

    kb_path = Path(args.kb)
    docs = load_knowledge_docs(kb_path)

    if args.query:
        print(json.dumps({"query": args.query, "top_docs": retrieve(args.query, docs, args.top_k)}, ensure_ascii=False, indent=2))
        return 0

    if args.facts and args.output:
        run_batch(Path(args.facts), Path(args.output), kb_path, args.top_k)
        return 0

    raise SystemExit("Use --query or (--facts and --output)")


if __name__ == "__main__":
    raise SystemExit(main())
