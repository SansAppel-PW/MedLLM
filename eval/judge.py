#!/usr/bin/env python3
"""LLM-as-a-Judge utilities for reproducible pairwise win-rate evaluation."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]


DEFAULT_BASE_URL = "https://api.gptsapi.net/v1"


@dataclass
class JudgeConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 256
    timeout_sec: float = 60.0
    criteria_version: str = "med_winrate_v1"


def _extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def build_judge_client() -> tuple[Any | None, str]:
    if load_dotenv is not None:
        load_dotenv()

    api_key = os.getenv("THIRD_PARTY_API_KEY", "").strip()
    if not api_key:
        return None, "missing THIRD_PARTY_API_KEY"

    try:
        from openai import OpenAI
    except ImportError:
        return None, "openai package is not installed"

    base_url = os.getenv("THIRD_PARTY_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL
    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, ""


def render_messages(query: str, answer_a: str, answer_b: str, criteria_version: str) -> list[dict[str, str]]:
    system = (
        "You are a strict medical QA judge. "
        "Evaluate answers by factuality, safety, and usefulness. "
        "Return ONLY JSON with keys: winner, score_a, score_b, reason."
    )
    user = "\n".join(
        [
            f"CriteriaVersion: {criteria_version}",
            "Task: Compare two candidate answers to a medical question.",
            "Scoring: 0-10 per answer, higher is better.",
            "winner must be one of: A, B, Tie.",
            "",
            f"Question:\n{query}",
            "",
            f"Answer A:\n{answer_a}",
            "",
            f"Answer B:\n{answer_b}",
            "",
            "JSON schema:",
            '{"winner":"A|B|Tie","score_a":0.0,"score_b":0.0,"reason":"<=80 words"}',
        ]
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def judge_one_pair(
    client: Any,
    query: str,
    answer_a: str,
    answer_b: str,
    config: JudgeConfig,
) -> dict[str, Any]:
    resp = client.chat.completions.create(
        model=config.model,
        messages=render_messages(query, answer_a, answer_b, config.criteria_version),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout_sec,
    )
    text = ""
    try:
        text = str(resp.choices[0].message.content or "")
    except Exception:
        text = ""

    payload = _extract_json_object(text)
    winner = str(payload.get("winner", "Tie")).strip()
    if winner not in {"A", "B", "Tie"}:
        winner = "Tie"

    try:
        score_a = float(payload.get("score_a", 0.0))
    except (TypeError, ValueError):
        score_a = 0.0
    try:
        score_b = float(payload.get("score_b", 0.0))
    except (TypeError, ValueError):
        score_b = 0.0

    reason = str(payload.get("reason", "")).strip()
    return {
        "winner": winner,
        "score_a": score_a,
        "score_b": score_b,
        "reason": reason,
        "raw_text": text,
    }


def evaluate_pairwise(
    *,
    queries: list[str],
    answers_a: list[str],
    answers_b: list[str],
    config: JudgeConfig,
    records_path: Path,
    summary_path: Path,
    max_samples: int = 0,
) -> dict[str, Any]:
    if not (len(queries) == len(answers_a) == len(answers_b)):
        return {"status": "invalid_input", "detail": "length mismatch"}

    client, err = build_judge_client()
    if client is None:
        summary = {"status": "skipped", "detail": err, "total": 0, "win_rate_a": 0.0}
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return summary

    n = len(queries)
    if max_samples > 0:
        n = min(n, max_samples)

    wins_a = 0
    wins_b = 0
    ties = 0
    records_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    with records_path.open("w", encoding="utf-8") as fw:
        for i in range(n):
            query = queries[i]
            a = answers_a[i]
            b = answers_b[i]
            try:
                judged = judge_one_pair(client, query, a, b, config)
            except Exception as exc:
                judged = {"winner": "Tie", "score_a": 0.0, "score_b": 0.0, "reason": f"judge_error:{exc}", "raw_text": ""}

            winner = judged["winner"]
            if winner == "A":
                wins_a += 1
            elif winner == "B":
                wins_b += 1
            else:
                ties += 1

            fw.write(
                json.dumps(
                    {
                        "index": i,
                        "query": query,
                        "answer_a": a,
                        "answer_b": b,
                        **judged,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    total = max(n, 1)
    win_rate_a = (wins_a + 0.5 * ties) / total
    summary = {
        "status": "ok",
        "model": config.model,
        "criteria_version": config.criteria_version,
        "total": n,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "ties": ties,
        "win_rate_a": win_rate_a,
        "records_path": str(records_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary

