#!/usr/bin/env python3
"""Common helpers for detection modules."""

from __future__ import annotations

import re
from typing import Iterable


def normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def tokenize(text: str) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    tokens = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+|\d+(?:\.\d+)?", text)
    return [t for t in tokens if t]


def jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def has_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)
