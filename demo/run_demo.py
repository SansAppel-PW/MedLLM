#!/usr/bin/env python3
"""Small scripted demo for MedLLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.serve.app import ask_once


SAMPLE_QUERIES = [
    "血友病患者可以使用阿司匹林吗？",
    "布洛芬成人常见剂量是多少？",
    "青霉素过敏患者可以用阿莫西林吗？",
]


def main() -> int:
    print("MedLLM 小型演示")
    for q in SAMPLE_QUERIES:
        res = ask_once(q)
        print("\n问题:", q)
        print("候选回答:", res["candidate_answer"])
        print("风险:", res["risk_level"], "分数:", res["risk_score"])
        print("最终输出:", res["final_answer"])
    print("\n演示完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
