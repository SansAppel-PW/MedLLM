#!/usr/bin/env python3
"""LLM-as-a-Judge helpers for pairwise answer comparison."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JUDGE_SYSTEM_PROMPT = """你是医疗问答评测裁判。
请比较 Answer A 和 Answer B 对于同一个问题的质量，重点按以下优先级打分：
1) 医学事实正确性（最高优先级）
2) 医疗安全性（是否有危险建议、禁忌冲突、剂量风险）
3) 实用性（是否可执行、表达清晰）

仅输出 JSON，不要输出任何额外文本，格式如下：
{"winner":"A|B|TIE","reason":"一句话简述原因","score_a":0-10,"score_b":0-10}
"""


@dataclass
class JudgeDecision:
    winner: str
    reason: str
    score_a: float
    score_b: float
    raw: dict[str, Any]


def _normalize_winner(raw_winner: Any) -> str:
    text = str(raw_winner or "").strip().upper()
    if text in {"A", "MODEL_A", "ANSWER_A", "1"}:
        return "A"
    if text in {"B", "MODEL_B", "ANSWER_B", "2"}:
        return "B"
    return "TIE"


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = (text or "").strip()
    if not cleaned:
        return {}
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    left = cleaned.find("{")
    right = cleaned.rfind("}")
    if left == -1 or right == -1 or right < left:
        return {}
    chunk = cleaned[left : right + 1]
    try:
        return json.loads(chunk)
    except json.JSONDecodeError:
        return {}


def parse_judge_decision(content: str) -> JudgeDecision:
    parsed = _extract_json(content)
    winner = _normalize_winner(parsed.get("winner"))
    reason = str(parsed.get("reason", "")).strip() or "No reason provided."
    try:
        score_a = float(parsed.get("score_a", 0.0))
    except (TypeError, ValueError):
        score_a = 0.0
    try:
        score_b = float(parsed.get("score_b", 0.0))
    except (TypeError, ValueError):
        score_b = 0.0
    score_a = max(0.0, min(10.0, score_a))
    score_b = max(0.0, min(10.0, score_b))
    return JudgeDecision(winner=winner, reason=reason, score_a=score_a, score_b=score_b, raw=parsed)


def _cache_key(model: str, query: str, answer_a: str, answer_b: str) -> str:
    payload = "\n".join([model, query, answer_a, answer_b])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_cache(cache_path: Path) -> dict[str, dict[str, Any]]:
    if not cache_path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with cache_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = str(row.get("key", ""))
            payload = row.get("payload")
            if key and isinstance(payload, dict):
                out[key] = payload
    return out


def _append_cache(cache_path: Path, key: str, payload: dict[str, Any]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"key": key, "payload": payload}, ensure_ascii=False) + "\n")


def _build_client() -> Any:
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ModuleNotFoundError("Missing dependency: python-dotenv") from exc

    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise ModuleNotFoundError("Missing dependency: openai") from exc

    load_dotenv()
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("Missing OPENAI_BASE_URL / OPENAI_API_KEY in environment.")
    return OpenAI(base_url=base_url, api_key=api_key)


def judge_pair(
    query: str,
    answer_a: str,
    answer_b: str,
    *,
    model: str = "gpt-4o-mini",
    max_retries: int = 3,
    retry_interval_sec: float = 2.0,
    cache_path: str = "reports/eval/judge_cache.jsonl",
) -> JudgeDecision:
    key = _cache_key(model, query, answer_a, answer_b)
    cache_file = Path(cache_path)
    cache = _read_cache(cache_file)
    cached = cache.get(key)
    if cached:
        return parse_judge_decision(json.dumps(cached, ensure_ascii=False))

    client = _build_client()
    user_prompt = (
        f"[Question]\n{query}\n\n"
        f"[Answer A]\n{answer_a}\n\n"
        f"[Answer B]\n{answer_b}\n"
    )

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = completion.choices[0].message.content or "{}"
            decision = parse_judge_decision(content)
            payload = dict(decision.raw)
            payload.setdefault("winner", decision.winner)
            payload.setdefault("reason", decision.reason)
            payload.setdefault("score_a", decision.score_a)
            payload.setdefault("score_b", decision.score_b)
            payload["model"] = model
            _append_cache(cache_file, key, payload)
            return JudgeDecision(
                winner=decision.winner,
                reason=decision.reason,
                score_a=decision.score_a,
                score_b=decision.score_b,
                raw=payload,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < max_retries:
                time.sleep(retry_interval_sec)

    assert last_error is not None
    raise RuntimeError(f"LLM judge failed after {max_retries} attempts: {last_error}") from last_error


def win_rate_from_decisions(decisions: list[JudgeDecision], winner_token: str) -> float:
    if not decisions:
        return 0.0
    wins = sum(1 for d in decisions if d.winner == winner_token)
    ties = sum(1 for d in decisions if d.winner == "TIE")
    return (wins + 0.5 * ties) / len(decisions)
