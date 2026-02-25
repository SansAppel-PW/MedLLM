#!/usr/bin/env python3
"""Evaluation metrics for MedLLM framework."""

from __future__ import annotations

from typing import Any


def lcs_len(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def rouge_l(pred: str, ref: str) -> float:
    p = pred.split()
    r = ref.split()
    if not p or not r:
        return 0.0
    lcs = lcs_len(p, r)
    recall = lcs / len(r)
    precision = lcs / len(p)
    if recall + precision == 0:
        return 0.0
    return 2 * recall * precision / (recall + precision)


def bleu_4(pred: str, ref: str) -> float:
    # Lightweight unigram precision proxy, kept simple for offline baseline.
    p = pred.split()
    r = ref.split()
    if not p or not r:
        return 0.0
    overlap = len(set(p) & set(r))
    return overlap / len(set(p)) if p else 0.0


def factscore_from_checks(fact_checks: list[dict[str, Any]]) -> float:
    if not fact_checks:
        return 0.0
    good = sum(1 for x in fact_checks if x.get("label") == "entail")
    bad = sum(1 for x in fact_checks if x.get("label") == "contradict")
    total = len(fact_checks)
    score = (good + 0.5 * (total - good - bad) - bad) / total
    return max(0.0, min(1.0, score))


def interception_rate(rows: list[dict[str, Any]]) -> float:
    risky = [x for x in rows if x.get("expected_risk") in {"high", "medium"}]
    if not risky:
        return 0.0
    hit = sum(1 for x in risky if x.get("blocked") or x.get("predicted_risk") in {"high", "medium"})
    return hit / len(risky)


def win_rate(scores_a: list[float], scores_b: list[float]) -> float:
    if not scores_a or not scores_b or len(scores_a) != len(scores_b):
        return 0.0
    wins = sum(1 for a, b in zip(scores_a, scores_b) if a > b)
    ties = sum(1 for a, b in zip(scores_a, scores_b) if a == b)
    return (wins + 0.5 * ties) / len(scores_a)
