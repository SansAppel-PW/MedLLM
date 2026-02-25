#!/usr/bin/env python3
"""Serving entry for MedLLM demo.

Provides:
- Optional FastAPI app (`/health`, `/ask`)
- CLI interactive demo fallback
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.detect.runtime_guard import guard_answer


def generate_candidate_answer(query: str) -> str:
    q = (query or "").strip()
    if not q:
        return "请提供具体问题。"

    if "阿司匹林" in q and "血友病" in q:
        return "阿司匹林可以用于缓解疼痛，血友病患者也可使用。"
    if "布洛芬" in q and ("剂量" in q or "怎么吃" in q):
        return "布洛芬常见成人剂量为每次200mg-400mg，请遵医嘱。"
    if "阿莫西林" in q and "过敏" in q:
        return "青霉素过敏人群可优先选择阿莫西林。"
    if "流感" in q and "奥司他韦" in q:
        return "奥司他韦可用于流感抗病毒治疗。"

    return "根据一般医学常识，该问题需要结合病史和体征综合判断，建议咨询医生。"


def ask_once(query: str, kg_path: str | Path = "data/kg/cmekg_demo.jsonl") -> dict[str, Any]:
    candidate = generate_candidate_answer(query)
    guarded = guard_answer(query=query, answer=candidate, kg_path=kg_path)
    guarded["candidate_answer"] = candidate
    return guarded


def interactive_cli(kg_path: str | Path) -> int:
    print("MedLLM 小型 Demo（输入 q 退出）")
    while True:
        query = input("\n问题> ").strip()
        if query.lower() in {"q", "quit", "exit"}:
            break
        result = ask_once(query, kg_path=kg_path)
        print("候选回答:", result["candidate_answer"])
        print("风险等级:", result["risk_level"], "| 分数:", result["risk_score"])
        print("最终输出:", result["final_answer"])
    return 0


def create_fastapi_app(kg_path: str | Path = "data/kg/cmekg_demo.jsonl"):
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI 未安装。请先执行 make setup。") from exc

    app = FastAPI(title="MedLLM Demo API", version="0.1.0")

    class AskRequest(BaseModel):
        query: str

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask")
    def ask(req: AskRequest) -> dict[str, Any]:
        return ask_once(req.query, kg_path=kg_path)

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="MedLLM serving entry")
    parser.add_argument("--query", default="", help="single query")
    parser.add_argument("--kg", default="data/kg/cmekg_demo.jsonl", help="knowledge base path")
    parser.add_argument("--print-json", action="store_true", help="print full json for single query")
    parser.add_argument("--demo", action="store_true", help="interactive cli demo")
    parser.add_argument("--serve", action="store_true", help="start FastAPI server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.query:
        out = ask_once(args.query, kg_path=args.kg)
        if args.print_json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(out["final_answer"])
            print(f"[risk={out['risk_level']} score={out['risk_score']}]")
        return 0

    if args.serve:
        try:
            import uvicorn
        except ModuleNotFoundError:
            print("uvicorn 未安装，请先执行 make setup", file=sys.stderr)
            return 1

        app = create_fastapi_app(kg_path=args.kg)
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    # default: interactive demo
    return interactive_cli(kg_path=args.kg)


if __name__ == "__main__":
    raise SystemExit(main())
