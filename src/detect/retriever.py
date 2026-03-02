#!/usr/bin/env python3
"""Lightweight lexical retrieval over KG / reference docs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import heapq
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


# Cache inverted index for large KB retrieval to avoid O(|query|*|docs|) scans.
_DOC_INDEX_CACHE: dict[int, tuple[int, dict[str, list[int]], dict[str, list[int]]]] = {}


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


def _build_doc_index(docs: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> tuple[dict[str, list[int]], dict[str, list[int]]]:
    key = id(docs)
    size = len(docs)
    cached = _DOC_INDEX_CACHE.get(key)
    if cached and cached[0] == size:
        return cached[1], cached[2]

    token_index: dict[str, list[int]] = defaultdict(list)
    hash_index: dict[str, list[int]] = defaultdict(list)
    for idx, doc in enumerate(docs):
        for tok in set(doc.get("tokens", [])):
            token_index[tok].append(idx)
        qh = str(doc.get("query_hash", "")).strip()
        if qh:
            hash_index[qh].append(idx)

    # Keep cache bounded for long-running processes.
    if len(_DOC_INDEX_CACHE) >= 8:
        _DOC_INDEX_CACHE.clear()
    _DOC_INDEX_CACHE[key] = (size, dict(token_index), dict(hash_index))
    return _DOC_INDEX_CACHE[key][1], _DOC_INDEX_CACHE[key][2]


def _iter_candidate_docs(
    docs: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    q_tokens: list[str],
    context_hash: str,
    top_k: int,
) -> list[dict[str, Any]] | tuple[dict[str, Any], ...]:
    # For small KB keep the exact full scan; for large KB use lexical candidate pruning.
    if len(docs) < 50_000:
        return docs

    token_index, hash_index = _build_doc_index(docs)
    counts: dict[int, int] = defaultdict(int)
    for tok in set(q_tokens):
        for idx in token_index.get(tok, []):
            counts[idx] += 1
    if context_hash:
        for idx in hash_index.get(context_hash, []):
            counts[idx] += 3

    if not counts:
        return docs

    # Retain enough candidates to keep recall while avoiding full-table scoring.
    max_candidates = max(6000, top_k * 1200)
    if len(counts) > max_candidates:
        picked = heapq.nlargest(max_candidates, counts.items(), key=lambda x: x[1])
        candidate_ids = [idx for idx, _ in picked]
    else:
        candidate_ids = list(counts.keys())
    return [docs[idx] for idx in candidate_ids]


def retrieve(
    query: str,
    docs: list[dict[str, Any]] | tuple[dict[str, Any], ...],
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

    candidate_docs = _iter_candidate_docs(docs, q_tokens, context_hash, top_k)
    scored = []
    for doc in candidate_docs:
        s = score_doc(q_tokens, q_norm, doc, context_hash=context_hash)
        if s >= min_score:
            scored.append(
                {
                    "doc_id": doc["doc_id"],
                    "text": doc["text"],
                    "score": round(s, 6),
                    "head": doc.get("head"),
                    "relation": doc.get("relation"),
                    "tail": doc.get("tail"),
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
