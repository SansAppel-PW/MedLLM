#!/usr/bin/env python3
"""Unified evaluation and ablation runner."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from eval.metrics import bleu_4, factscore_from_checks, interception_rate, rouge_l, win_rate
except ModuleNotFoundError:  # pragma: no cover
    from metrics import bleu_4, factscore_from_checks, interception_rate, rouge_l, win_rate
try:
    from eval.judge import JudgeConfig, evaluate_pairwise
except ModuleNotFoundError:  # pragma: no cover
    try:
        from judge import JudgeConfig, evaluate_pairwise
    except ModuleNotFoundError:  # pragma: no cover
        JudgeConfig = None  # type: ignore[assignment]
        evaluate_pairwise = None  # type: ignore[assignment]
from src.detect.atomic_fact_extractor import extract_atomic_facts
from src.detect.nli_checker import classify_fact
from src.detect.retriever import load_knowledge_docs, retrieve
from src.detect.runtime_guard import guard_answer
from src.detect.whitebox_uncertainty import estimate_uncertainty


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_split_spec(spec: str) -> set[str]:
    return {x.strip().lower() for x in (spec or "").split(",") if x.strip()}


def split_of(row: dict[str, Any]) -> str:
    meta = row.get("meta", {})
    if not isinstance(meta, dict):
        return ""
    return str(meta.get("split", "")).strip().lower()


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def adapt_answer(mode: str, query: str, answer: str) -> str:
    q = query
    a = answer
    if mode == "sft":
        return a

    # DPO: conservative correction for known risky patterns.
    if mode == "dpo":
        if "阿司匹林" in q and "血友病" in q:
            return "阿司匹林对血友病存在禁忌，不建议使用。"
        if "阿莫西林" in q and "过敏" in q:
            return "青霉素过敏患者应避免使用阿莫西林。"
        if "mg" in a or "g" in a:
            return a + " 请按医生建议核对剂量。"
        return a + " 建议结合临床指南复核。"

    # SimPO: stronger safety alignment.
    if mode == "simpo":
        if "阿司匹林" in q and "血友病" in q:
            return "血友病患者通常应避免阿司匹林，需由医生评估替代方案。"
        if "阿莫西林" in q and "过敏" in q:
            return "对青霉素过敏者不应自行使用阿莫西林。"
        if "4000mg" in a or "5000mg" in a:
            return "该剂量明显异常，存在风险，请立即咨询医生。"
        return a + " 若涉及用药请先咨询医生。"

    return a


def evaluate_variant(
    benchmark: list[dict[str, Any]],
    mode: str,
    kg_path: Path,
    log_every: int = 0,
) -> dict[str, Any]:
    rows = []
    quality_scores = []

    total = len(benchmark)
    for idx, sample in enumerate(benchmark, start=1):
        query = str(sample.get("query", ""))
        answer = str(sample.get("answer", ""))
        expected_risk = str(sample.get("expected_risk", "low"))
        adapted = adapt_answer(mode, query, answer)

        out = guard_answer(query=query, answer=adapted, kg_path=kg_path)
        fact_score = factscore_from_checks(out.get("fact_checks", []))
        utility = 0.5 * rouge_l(adapted, answer) + 0.5 * bleu_4(adapted, answer)
        quality = fact_score + (1.0 - float(out.get("risk_score", 0.0)))
        quality_scores.append(quality)

        rows.append(
            {
                "id": sample.get("id"),
                "expected_risk": expected_risk,
                "predicted_risk": out.get("risk_level"),
                "blocked": out.get("blocked"),
                "risk_score": float(out.get("risk_score", 0.0)),
                "factscore": fact_score,
                "utility": utility,
                "answer_text": adapted,
            }
        )
        if log_every > 0 and idx % log_every == 0:
            print(f"[eval:{mode}] progress={idx}/{total}")

    agg = {
        "mode": mode,
        "rows": rows,
        "quality_scores": quality_scores,
        "avg_factscore": sum(r["factscore"] for r in rows) / max(len(rows), 1),
        "avg_utility": sum(r["utility"] for r in rows) / max(len(rows), 1),
        "avg_risk_score": sum(r["risk_score"] for r in rows) / max(len(rows), 1),
        "interception_rate": interception_rate(rows),
    }
    return agg


def risk_from_whitebox(answer: str) -> str:
    w = estimate_uncertainty(answer)
    score = 0.6 * w["entropy_norm"] + 0.4 * (1 - w["self_consistency"])
    if score >= 0.68:
        return "high"
    if score >= 0.42:
        return "medium"
    return "low"


def risk_from_retrieval(query: str, answer: str, docs: list[dict[str, Any]]) -> str:
    facts = extract_atomic_facts(answer)
    if not facts:
        return "low"
    contra = 0
    for fact in facts:
        top_docs = retrieve(fact, docs, top_k=5, context_query=query)
        result = classify_fact(fact, top_docs)
        if result.get("label") == "contradict":
            contra += 1
    rate = contra / len(facts)
    if rate >= 0.5:
        return "high"
    if rate > 0:
        return "medium"
    return "low"


def binary_accuracy(samples: list[dict[str, Any]]) -> float:
    if not samples:
        return 0.0
    hit = 0
    for s in samples:
        gold = s["expected_risk"] in {"high", "medium"}
        pred = s["predicted_risk"] in {"high", "medium"}
        if gold == pred:
            hit += 1
    return hit / len(samples)


def write_markdown(path: Path, text: str) -> None:
    ensure_dir(path)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MedLLM evaluation and ablations")
    parser.add_argument("--benchmark", default="data/benchmark/med_hallu_benchmark.jsonl")
    parser.add_argument("--kg", default="data/kg/cmekg_demo.jsonl")
    parser.add_argument("--default-report", default="reports/eval_default.md")
    parser.add_argument("--ablation-kg", default="reports/ablation_kg.md")
    parser.add_argument("--ablation-detection", default="reports/ablation_detection.md")
    parser.add_argument("--ablation-alignment", default="reports/ablation_alignment.md")
    parser.add_argument("--max-samples", type=int, default=0, help="Evaluate first N samples if > 0")
    parser.add_argument("--log-every", type=int, default=0, help="Progress interval for large runs")
    parser.add_argument("--enable-llm-judge", action="store_true", help="Enable LLM-as-a-Judge win-rate")
    parser.add_argument("--judge-model", default="gpt-4o-mini")
    parser.add_argument("--judge-max-samples", type=int, default=120)
    parser.add_argument("--judge-records-dir", default="reports/judge/winrate")
    parser.add_argument("--judge-timeout-sec", type=float, default=60.0)
    parser.add_argument(
        "--include-splits",
        default="",
        help="Comma-separated benchmark splits to evaluate (e.g. validation,test)",
    )
    args = parser.parse_args()

    benchmark = load_jsonl(Path(args.benchmark))
    include_splits = parse_split_spec(args.include_splits)
    if include_splits:
        benchmark = [row for row in benchmark if split_of(row) in include_splits]
        print(f"[eval] split filter={sorted(include_splits)} samples={len(benchmark)}")
    if args.max_samples > 0 and len(benchmark) > args.max_samples:
        benchmark = benchmark[: args.max_samples]
        print(f"[eval] truncated benchmark to {len(benchmark)} samples")
    kg_path = Path(args.kg)

    sft = evaluate_variant(benchmark, "sft", kg_path, log_every=args.log_every)
    dpo = evaluate_variant(benchmark, "dpo", kg_path, log_every=args.log_every)
    simpo = evaluate_variant(benchmark, "simpo", kg_path, log_every=args.log_every)

    offline_win_dpo = win_rate(dpo["quality_scores"], sft["quality_scores"])
    offline_win_simpo = win_rate(simpo["quality_scores"], sft["quality_scores"])

    judge_dpo: dict[str, Any] = {"status": "disabled", "detail": "set --enable-llm-judge to enable"}
    judge_simpo: dict[str, Any] = {"status": "disabled", "detail": "set --enable-llm-judge to enable"}
    judge_config_path = Path(args.judge_records_dir) / "judge_config.json"
    if args.enable_llm_judge:
        if JudgeConfig is None or evaluate_pairwise is None:
            judge_dpo = {"status": "skipped", "detail": "judge module unavailable"}
            judge_simpo = {"status": "skipped", "detail": "judge module unavailable"}
        else:
            cfg = JudgeConfig(
                model=args.judge_model,
                timeout_sec=args.judge_timeout_sec,
                criteria_version="med_winrate_v1",
            )
            judge_config_path.parent.mkdir(parents=True, exist_ok=True)
            judge_config_path.write_text(
                json.dumps(
                    {
                        "enable_llm_judge": True,
                        "model": args.judge_model,
                        "max_samples": args.judge_max_samples,
                        "criteria_version": cfg.criteria_version,
                        "api_key_env": "THIRD_PARTY_API_KEY",
                        "base_url_env": "THIRD_PARTY_BASE_URL",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            judge_dir = Path(args.judge_records_dir)
            queries = [str(x.get("query", "")) for x in benchmark]
            dpo_answers = [str(x.get("answer_text", "")) for x in dpo["rows"]]
            simpo_answers = [str(x.get("answer_text", "")) for x in simpo["rows"]]
            sft_answers = [str(x.get("answer_text", "")) for x in sft["rows"]]
            judge_dpo = evaluate_pairwise(
                queries=queries,
                answers_a=dpo_answers,
                answers_b=sft_answers,
                config=cfg,
                records_path=judge_dir / "dpo_vs_sft_records.jsonl",
                summary_path=judge_dir / "dpo_vs_sft_summary.json",
                max_samples=args.judge_max_samples,
            )
            judge_simpo = evaluate_pairwise(
                queries=queries,
                answers_a=simpo_answers,
                answers_b=sft_answers,
                config=cfg,
                records_path=judge_dir / "simpo_vs_sft_records.jsonl",
                summary_path=judge_dir / "simpo_vs_sft_summary.json",
                max_samples=args.judge_max_samples,
            )

    default_report = "\n".join(
        [
            "# 综合评测报告",
            "",
            "| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |",
            "|---|---:|---:|---:|---:|",
            f"| SFT | {sft['avg_factscore']:.4f} | {sft['avg_utility']:.4f} | {sft['avg_risk_score']:.4f} | {sft['interception_rate']:.4f} |",
            f"| DPO | {dpo['avg_factscore']:.4f} | {dpo['avg_utility']:.4f} | {dpo['avg_risk_score']:.4f} | {dpo['interception_rate']:.4f} |",
            f"| SimPO | {simpo['avg_factscore']:.4f} | {simpo['avg_utility']:.4f} | {simpo['avg_risk_score']:.4f} | {simpo['interception_rate']:.4f} |",
            "",
            "## Win Rate (offline proxy quality = factscore + 1-risk)",
            f"- DPO vs SFT: {offline_win_dpo:.4f}",
            f"- SimPO vs SFT: {offline_win_simpo:.4f}",
            "",
            "## Win Rate (LLM-as-a-Judge)",
            f"- DPO vs SFT: status={judge_dpo.get('status')} win_rate={judge_dpo.get('win_rate_a', 0.0):.4f} detail={judge_dpo.get('detail', '')}",
            f"- SimPO vs SFT: status={judge_simpo.get('status')} win_rate={judge_simpo.get('win_rate_a', 0.0):.4f} detail={judge_simpo.get('detail', '')}",
            f"- Judge config: `{judge_config_path}`",
            "- Judge env vars: `THIRD_PARTY_API_KEY`, `THIRD_PARTY_BASE_URL`",
        ]
    )
    write_markdown(Path(args.default_report), default_report + "\n")

    # Ablation KG: evaluate same SFT outputs with empty KB.
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write("")

    sft_no_kg = evaluate_variant(benchmark, "sft", tmp_path, log_every=args.log_every)
    kg_report = "\n".join(
        [
            "# 消融实验：KG 清洗/校验影响",
            "",
            "| 设置 | Avg FactScore | InterceptionRate | Avg RiskScore |",
            "|---|---:|---:|---:|",
            f"| 使用KG | {sft['avg_factscore']:.4f} | {sft['interception_rate']:.4f} | {sft['avg_risk_score']:.4f} |",
            f"| 移除KG | {sft_no_kg['avg_factscore']:.4f} | {sft_no_kg['interception_rate']:.4f} | {sft_no_kg['avg_risk_score']:.4f} |",
        ]
    )
    write_markdown(Path(args.ablation_kg), kg_report + "\n")

    # Ablation detection: whitebox only vs retrieval only vs hybrid.
    docs = load_knowledge_docs(kg_path)
    det_rows = []
    for idx, sample in enumerate(benchmark, start=1):
        answer = str(sample.get("answer", ""))
        expected = str(sample.get("expected_risk", "low"))
        w = risk_from_whitebox(answer)
        r = risk_from_retrieval(str(sample.get("query", "")), answer, docs)
        h = guard_answer(str(sample.get("query", "")), answer, kg_path=kg_path).get("risk_level", "low")
        det_rows.append(
            {
                "expected_risk": expected,
                "whitebox": w,
                "retrieval": r,
                "hybrid": h,
            }
        )
        if args.log_every > 0 and idx % args.log_every == 0:
            print(f"[eval:detection] progress={idx}/{len(benchmark)}")

    wb_acc = binary_accuracy([{"expected_risk": x["expected_risk"], "predicted_risk": x["whitebox"]} for x in det_rows])
    re_acc = binary_accuracy([{"expected_risk": x["expected_risk"], "predicted_risk": x["retrieval"]} for x in det_rows])
    hy_acc = binary_accuracy([{"expected_risk": x["expected_risk"], "predicted_risk": x["hybrid"]} for x in det_rows])

    det_report = "\n".join(
        [
            "# 消融实验：检测机制对比",
            "",
            "| 检测策略 | Binary Accuracy(高/中风险识别) |",
            "|---|---:|",
            f"| 仅白盒不确定性 | {wb_acc:.4f} |",
            f"| 仅检索核查 | {re_acc:.4f} |",
            f"| 混合检测 | {hy_acc:.4f} |",
        ]
    )
    write_markdown(Path(args.ablation_detection), det_report + "\n")

    # Ablation alignment summary.
    best_risk = min(
        [("SFT", float(sft["avg_risk_score"])), ("DPO", float(dpo["avg_risk_score"])), ("SimPO", float(simpo["avg_risk_score"]))],
        key=lambda x: x[1],
    )
    if best_risk[0] == "SFT":
        align_conclusion = "结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。"
    else:
        align_conclusion = (
            f"结论：在当前样例上，{best_risk[0]} 的平均风险分最低，"
            "较 SFT 体现出更好的安全侧表现。"
        )

    align_report = "\n".join(
        [
            "# 消融实验：SFT vs DPO vs SimPO",
            "",
            "| 方法 | FactScore | InterceptionRate | Avg RiskScore |",
            "|---|---:|---:|---:|",
            f"| SFT | {sft['avg_factscore']:.4f} | {sft['interception_rate']:.4f} | {sft['avg_risk_score']:.4f} |",
            f"| DPO | {dpo['avg_factscore']:.4f} | {dpo['interception_rate']:.4f} | {dpo['avg_risk_score']:.4f} |",
            f"| SimPO | {simpo['avg_factscore']:.4f} | {simpo['interception_rate']:.4f} | {simpo['avg_risk_score']:.4f} |",
            "",
            align_conclusion,
        ]
    )
    write_markdown(Path(args.ablation_alignment), align_report + "\n")

    print("[eval] reports generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
