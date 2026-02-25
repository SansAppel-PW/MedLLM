#!/usr/bin/env python3
"""Lightweight retrieval module over KG-style knowledge base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from .common import jaccard_similarity, tokenize
except ImportError:  # pragma: no cover
    from common import jaccard_similarity, tokenize


RELATION_ZH = {
    "treats": "可用于治疗",
    "contraindicated_for": "禁用于",
    "dosage_range_mg": "推荐剂量范围",
    "dosage": "用量",
}


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
        rel_text = RELATION_ZH.get(r, r)
        text = f"{h}{rel_text}{t}" if h and t else str(row)
        docs.append(
            {
                "doc_id": f"kg_{i}",
                "text": text,
                "head": h,
                "relation": r,
                "tail": t,
                "tokens": tokenize(text),
            }
        )
    return docs


def score_doc(query: str, doc: dict[str, Any]) -> float:
    q_tokens = tokenize(query)
    base = jaccard_similarity(q_tokens, doc.get("tokens", []))
    bonus = 0.0
    if doc.get("head") and doc["head"] in query:
        bonus += 0.2
    if doc.get("tail") and doc["tail"] in query:
        bonus += 0.2
    return base + bonus


def retrieve(query: str, docs: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    scored = []
    for doc in docs:
        s = score_doc(query, doc)
        if s > 0:
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
