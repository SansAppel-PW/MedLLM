#!/usr/bin/env python3
"""Runtime hallucination guard: whitebox + retrieval fact check + risk fusion."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
import re
import tempfile
from pathlib import Path
from typing import Any

try:
    from .atomic_fact_extractor import extract_atomic_facts
    from .nli_checker import classify_fact
    from .retriever import load_knowledge_docs, retrieve
    from .risk_fusion import fuse_one
    from .whitebox_uncertainty import estimate_uncertainty
except ImportError:  # pragma: no cover
    from atomic_fact_extractor import extract_atomic_facts
    from nli_checker import classify_fact
    from retriever import load_knowledge_docs, retrieve
    from risk_fusion import fuse_one
    from whitebox_uncertainty import estimate_uncertainty


SAFE_BLOCK_MSG = (
    "检测到回答可能包含高风险医疗幻觉或事实冲突。"
    "请勿依据该内容自行诊疗，建议咨询持证医生并参考权威指南。"
)

SAFE_WARN_SUFFIX = "\n\n[风险提示] 该回答存在不确定性，请结合专业医生建议进行复核。"
MCQ_OPTION_RE = re.compile(r"(?im)^\s*([A-D])[\.\)]\s*(.+?)\s*$")
ANSWER_SIGNAL_RE = re.compile(
    r"(?is)(?:正确答案|correct answer)\s*[:：]?\s*(?:([A-D])[\.\)]\s*)?(.*)"
)


@lru_cache(maxsize=8)
def cached_docs(kg_path: str) -> tuple[dict[str, Any], ...]:
    docs = load_knowledge_docs(Path(kg_path))
    return tuple(docs)


def parse_mcq_options(query: str) -> dict[str, str]:
    options: dict[str, str] = {}
    for letter, text in MCQ_OPTION_RE.findall(query or ""):
        key = (letter or "").upper()
        content = (text or "").strip()
        if key and content:
            options[key] = content
    return options


def parse_answer_signal(answer: str) -> tuple[str | None, str]:
    text = (answer or "").strip()
    match = ANSWER_SIGNAL_RE.search(text)
    if not match:
        return None, text

    letter = (match.group(1) or "").upper() or None
    payload = (match.group(2) or "").strip()
    if letter is None:
        fallback = re.match(r"^\s*([A-D])[\.\)]\s*(.*)$", payload, flags=re.IGNORECASE)
        if fallback:
            letter = fallback.group(1).upper()
            payload = (fallback.group(2) or "").strip()
    return letter, payload


def mcq_format_signal(query: str, answer: str) -> dict[str, Any]:
    options = parse_mcq_options(query)
    if not options:
        return {"mcq_detected": 0.0, "format_mismatch": 0.0}

    letter, payload = parse_answer_signal(answer)
    mismatch = 0.0
    if letter is None:
        mismatch = 1.0
        reason = "missing_option_letter"
    elif letter not in options:
        mismatch = 1.0
        reason = "invalid_option_letter"
    else:
        reason = "ok"
        option_text = options.get(letter, "")
        if payload and option_text and payload.lower() not in option_text.lower():
            # Payload is optional in multiple-choice short answers. Only mark a
            # soft mismatch when explicit payload conflicts with the selected option.
            mismatch = 0.5
            reason = "payload_option_mismatch"

    return {
        "mcq_detected": 1.0,
        "format_mismatch": mismatch,
        "option_letter_present": 1.0 if letter else 0.0,
        "format_reason": reason,
    }


def guard_answer(
    query: str,
    answer: str,
    kg_path: str | Path = "data/kg/cmekg_demo.jsonl",
    top_k: int = 5,
    high_threshold: float = 0.58,
    medium_threshold: float = 0.40,
) -> dict[str, Any]:
    answer = (answer or "").strip()
    query = (query or "").strip()

    whitebox = estimate_uncertainty(answer)
    facts = extract_atomic_facts(answer)
    if not facts and answer:
        facts = [answer]

    kg_abs = str(Path(kg_path).resolve())
    docs = list(cached_docs(kg_abs))
    nli_results = []
    for fact in facts:
        top_docs = retrieve(fact, docs, top_k=top_k, context_query=query)
        nli_results.append(classify_fact(fact, top_docs))

    fused = fuse_one(
        rec_id="single",
        whitebox_row={"id": "single", **whitebox},
        nli_row={"id": "single", "fact_results": nli_results},
        high=high_threshold,
        medium=medium_threshold,
    )

    risk_level = fused.get("risk_level", "low")
    risk_score = float(fused.get("risk_score", 0.0))
    signals = dict(fused.get("signals", {}))
    mcq_signal = mcq_format_signal(query, answer)
    signals.update(mcq_signal)

    # Strongly overconfident clinical assertions should at least be warned.
    if risk_level == "low" and float(whitebox.get("overconfidence_flag", 0.0)) >= 1.0:
        risk_level = "medium"
        risk_score = max(risk_score, medium_threshold)
        signals["overconfidence_escalation"] = 1.0

    if risk_level == "low" and float(mcq_signal.get("format_mismatch", 0.0)) >= 1.0:
        risk_level = "medium"
        risk_score = max(risk_score, medium_threshold + 0.05)
        signals["mcq_format_escalation"] = 1.0

    blocked = risk_level == "high"
    warning = risk_level == "medium"

    if blocked:
        final_answer = SAFE_BLOCK_MSG
    elif warning:
        final_answer = answer + SAFE_WARN_SUFFIX
    else:
        final_answer = answer

    return {
        "query": query,
        "original_answer": answer,
        "final_answer": final_answer,
        "blocked": blocked,
        "risk_level": risk_level,
        "risk_score": round(risk_score, 6),
        "signals": signals,
        "facts": facts,
        "fact_checks": nli_results,
    }


def run_batch(input_path: Path, output_path: Path, kg_path: Path, top_k: int) -> None:
    rows = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    out = []
    for row in rows:
        result = guard_answer(
            query=str(row.get("query", "")),
            answer=str(row.get("answer", "")),
            kg_path=kg_path,
            top_k=top_k,
        )
        result["id"] = row.get("id")
        if "expected_risk" in row:
            result["expected_risk"] = row.get("expected_risk")
        out.append(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[runtime-guard] input={len(rows)} output={len(out)} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime hallucination guard")
    parser.add_argument("--query", default="", help="Single query")
    parser.add_argument("--answer", default="", help="Single model answer")
    parser.add_argument("--kg", default="data/kg/cmekg_demo.jsonl", help="Knowledge base")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--input", default="", help="Batch input jsonl")
    parser.add_argument("--output", default="", help="Batch output jsonl")
    args = parser.parse_args()

    if args.query or args.answer:
        result = guard_answer(args.query, args.answer, kg_path=args.kg, top_k=args.top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.input and args.output:
        run_batch(Path(args.input), Path(args.output), Path(args.kg), args.top_k)
        return 0

    # Interactive fallback for quick manual demo.
    print("进入交互模式，输入 q 退出。")
    kg = Path(args.kg)
    while True:
        query = input("\n问题> ").strip()
        if query.lower() in {"q", "quit", "exit"}:
            break
        answer = input("候选回答> ").strip()
        result = guard_answer(query=query, answer=answer, kg_path=kg, top_k=args.top_k)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
