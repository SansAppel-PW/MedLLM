#!/usr/bin/env python3
"""Audit project consistency against opening proposal constraints."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PASS = "PASS"
PARTIAL = "PARTIAL"
FAIL = "FAIL"


@dataclass
class CheckResult:
    id: str
    requirement: str
    status: str
    detail: str
    evidence: list[str]
    source_refs: list[str]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def has_all(text: str, items: list[str]) -> bool:
    return all(x in text for x in items)


def exists_all(root: Path, rel_paths: list[str]) -> tuple[bool, list[str]]:
    missing = [p for p in rel_paths if not (root / p).exists()]
    return len(missing) == 0, missing


def row_has_model(rows: list[dict[str, Any]], keyword: str) -> bool:
    keyword = keyword.lower()
    for row in rows:
        if keyword in str(row.get("model", "")).lower():
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check alignment with opening proposal requirements")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-md", default="reports/opening_alignment_audit.md")
    parser.add_argument("--out-json", default="reports/opening_alignment_audit.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results: list[CheckResult] = []

    # A01: Repo safety and secret/data guarding.
    gi_path = root / ".gitignore"
    guard_path = root / "scripts/repo_guard.py"
    gi = gi_path.read_text(encoding="utf-8") if gi_path.exists() else ""
    gi_needed = [".env", "/data/", "/checkpoints/", "*.safetensors", "*.ckpt"]
    gi_ok = has_all(gi, gi_needed)
    if guard_path.exists() and gi_ok:
        results.append(
            CheckResult(
                id="A01",
                requirement="仓库安全防护（数据/权重/密钥不得入库）",
                status=PASS,
                detail="Repo Guard 与 .gitignore 关键规则存在。",
                evidence=["scripts/repo_guard.py", ".gitignore"],
                source_refs=["【DOCX | 研究内容与难点 | 段落#1】"],
            )
        )
    else:
        results.append(
            CheckResult(
                id="A01",
                requirement="仓库安全防护（数据/权重/密钥不得入库）",
                status=FAIL,
                detail="Repo Guard 或 .gitignore 关键规则缺失。",
                evidence=["scripts/repo_guard.py", ".gitignore"],
                source_refs=["【DOCX | 研究内容与难点 | 段落#1】"],
            )
        )

    # A02: Three-layer system pipeline.
    layer_needed = [
        "scripts/data/run_data_governance_pipeline.py",
        "scripts/train/run_small_real_pipeline.sh",
        "scripts/train/run_real_alignment_pipeline.sh",
        "scripts/eval/run_thesis_pipeline.sh",
        "scripts/run_autonomous_iteration.sh",
    ]
    ok, missing = exists_all(root, layer_needed)
    results.append(
        CheckResult(
            id="A02",
            requirement="三层闭环（数据治理-检测-对齐）可执行",
            status=PASS if ok else FAIL,
            detail="闭环入口齐全。" if ok else f"缺失入口: {', '.join(missing)}",
            evidence=layer_needed,
            source_refs=["【PDF | 页码p10 | 段落#1】", "【DOCX | 题目与任务定义 | 段落#1】"],
        )
    )

    # A03: Real dataset evidence.
    real_summary = load_json(root / "reports/real_dataset_summary.json")
    if real_summary and int(real_summary.get("train_count", 0)) > 0:
        detail = (
            f"real数据可用 train/dev/test="
            f"{real_summary.get('train_count')}/{real_summary.get('dev_count')}/{real_summary.get('test_count')}。"
        )
        status = PASS
    else:
        detail = "缺少 real_dataset_summary 或样本计数为0。"
        status = FAIL
    results.append(
        CheckResult(
            id="A03",
            requirement="真实数据构建与版本化可追溯",
            status=status,
            detail=detail,
            evidence=["reports/real_dataset_summary.json", "reports/real_dataset_report.md"],
            source_refs=["【PDF | 页码p12 | 段落#1】"],
        )
    )

    # A04: Real training evidence chain.
    thesis_summary = load_json(root / "reports/thesis_assets/thesis_ready_summary.json") or {}
    latest_small = thesis_summary.get("latest_small_real_run")
    small_ok = False
    small_evidence: list[str] = []
    if latest_small:
        needed = [
            f"reports/training/{latest_small}_metrics.json",
            f"reports/small_real/{latest_small}/loss_curve.csv",
            f"reports/small_real/{latest_small}/loss_curve.png",
            f"reports/small_real/{latest_small}/run_card.json",
        ]
        small_ok, _ = exists_all(root, needed)
        small_evidence = needed
    dpo_real = load_json(root / "reports/training/dpo_real_metrics.json")
    dpo_ok = bool(dpo_real and dpo_real.get("simulation") is False and int(dpo_real.get("pair_count", 0)) > 0)
    status = PASS if small_ok and dpo_ok else FAIL
    detail = "small-real 与 real DPO 证据链齐全。" if status == PASS else "small-real 或 real DPO 证据链缺失。"
    results.append(
        CheckResult(
            id="A04",
            requirement="真实训练证据链（loss/ckpt/eval/run-card）",
            status=status,
            detail=detail,
            evidence=small_evidence + ["reports/training/dpo_real_metrics.json"],
            source_refs=["【PDF | 页码p11 | 段落#1】", "【DOCX | 方法与实验设计 | 段落#1】"],
        )
    )

    # A05: Alignment method coverage.
    simpo = load_json(root / "reports/training/simpo_metrics.json")
    kto = load_json(root / "reports/training/kto_metrics.json")
    if dpo_ok and simpo and kto:
        sim_proxy = bool(simpo.get("simulation") is True)
        kto_proxy = bool(kto.get("simulation") is True)
        if sim_proxy or kto_proxy:
            status = PARTIAL
            detail = "DPO为真实训练；SimPO/KTO 当前为 proxy，方法覆盖完整但真实度部分不足。"
        else:
            status = PASS
            detail = "DPO/SimPO/KTO 均为真实训练。"
    else:
        status = FAIL
        detail = "缺少对齐方法指标文件，无法证明 DPO/SimPO/KTO 覆盖。"
    results.append(
        CheckResult(
            id="A05",
            requirement="对齐方法覆盖（SFT + DPO/SimPO/KTO）",
            status=status,
            detail=detail,
            evidence=[
                "reports/training/dpo_real_metrics.json",
                "reports/training/simpo_metrics.json",
                "reports/training/kto_metrics.json",
                "reports/alignment_compare.md",
            ],
            source_refs=["【PDF | 页码p11 | 段落#1】", "【DOCX | 方法与实验设计 | 段落#1】"],
        )
    )

    # A06: Baseline coverage in audit table.
    baseline_payload = load_json(root / "reports/thesis_assets/tables/baseline_audit_table.json") or {}
    if isinstance(baseline_payload, dict):
        rows = baseline_payload.get("all", [])
    elif isinstance(baseline_payload, list):
        rows = baseline_payload
    else:
        rows = []
    baseline_ok = all(
        [
            row_has_model(rows, "med-palm"),
            row_has_model(rows, "chatdoctor"),
            row_has_model(rows, "huatuogpt"),
            row_has_model(rows, "disc"),
            row_has_model(rows, "qwen"),
        ]
    )
    results.append(
        CheckResult(
            id="A06",
            requirement="Baseline 覆盖（Med-PaLM/ChatDoctor/HuatuoGPT/DISC/Qwen）",
            status=PASS if baseline_ok else FAIL,
            detail="baseline 覆盖完整。" if baseline_ok else "baseline 覆盖不完整。",
            evidence=["reports/thesis_assets/tables/baseline_audit_table.json"],
            source_refs=["【PDF | 页码p5 | 段落#1】", "【PDF | 页码p12 | 段落#1】"],
        )
    )

    # A07: Metric coverage.
    eval_default = (root / "reports/eval_default.md").read_text(encoding="utf-8") if (root / "reports/eval_default.md").exists() else ""
    main_real_csv = (root / "reports/thesis_assets/tables/main_results_real.csv").read_text(encoding="utf-8") if (root / "reports/thesis_assets/tables/main_results_real.csv").exists() else ""
    metric_ok = has_all(eval_default, ["FactScore", "Win Rate", "InterceptionRate"]) and ("rouge_l_f1" in main_real_csv)
    results.append(
        CheckResult(
            id="A07",
            requirement="评测指标覆盖（FactScore/WinRate/Rouge-L/Interception）",
            status=PASS if metric_ok else FAIL,
            detail="指标覆盖满足开题口径。" if metric_ok else "指标覆盖不足或产物缺失。",
            evidence=["reports/eval_default.md", "reports/thesis_assets/tables/main_results_real.csv"],
            source_refs=["【PDF | 页码p13 | 段落#1】", "【DOCX | 方法与实验设计 | 段落#1】"],
        )
    )

    # A08: WinRate judge consistency (proposal mentions GPT-4 judge).
    env_example = (root / ".env.example").read_text(encoding="utf-8") if (root / ".env.example").exists() else ""
    code_text = "\n".join(
        [
            (root / "scripts/eval/run_sota_compare.py").read_text(encoding="utf-8")
            if (root / "scripts/eval/run_sota_compare.py").exists()
            else "",
            (root / "eval/metrics.py").read_text(encoding="utf-8") if (root / "eval/metrics.py").exists() else "",
            (root / "eval/judge.py").read_text(encoding="utf-8") if (root / "eval/judge.py").exists() else "",
            (root / "eval/run_eval.py").read_text(encoding="utf-8") if (root / "eval/run_eval.py").exists() else "",
        ]
    )
    has_judge_runtime = all(
        [
            "THIRD_PARTY_API_KEY" in code_text,
            "THIRD_PARTY_BASE_URL" in code_text,
            "OpenAI(" in code_text,
            "LLM-as-a-Judge" in code_text or "enable-llm-judge" in code_text,
            "THIRD_PARTY_API_KEY" in env_example,
        ]
    )
    if has_judge_runtime:
        status = PASS
        detail = "存在可追溯 LLM-as-a-Judge 实现（含 .env 注入与落盘记录入口）。"
    else:
        status = PARTIAL
        detail = "当前 WinRate 为离线规则口径，尚未落地 GPT-4 Judge 版本。"
    results.append(
        CheckResult(
            id="A08",
            requirement="WinRate 与开题 GPT-4 Judge 口径一致性",
            status=status,
            detail=detail,
            evidence=[
                "eval/judge.py",
                "eval/run_eval.py",
                ".env.example",
                "reports/eval_default.md",
            ],
            source_refs=["【PDF | 页码p13 | 段落#1】"],
        )
    )

    # A09: real/proxy separation.
    dual_ok, _ = exists_all(
        root,
        [
            "reports/thesis_assets/tables/main_results_real.csv",
            "reports/thesis_assets/tables/main_results_proxy.csv",
            "reports/thesis_assets/tables/main_results_dual_view.md",
            "reports/thesis_assets/tables/baseline_real_mainline.csv",
            "reports/thesis_assets/tables/baseline_proxy_background.csv",
            "reports/thesis_assets/tables/baseline_audit_dual_view.md",
        ],
    )
    results.append(
        CheckResult(
            id="A09",
            requirement="real/proxy 结果分层展示与口径隔离",
            status=PASS if dual_ok else FAIL,
            detail="双层表已形成。" if dual_ok else "缺少 real/proxy 双层表产物。",
            evidence=[
                "reports/thesis_assets/tables/main_results_dual_view.md",
                "reports/thesis_assets/tables/baseline_audit_dual_view.md",
            ],
            source_refs=["【PPT | 页码15 | 要点#7】"],
        )
    )

    # A10: full experiment feasibility under current resources.
    layer_b_metrics = root / "reports/training/layer_b_qwen25_7b_sft_metrics.json"
    qwen_blocker = root / "reports/small_real/qwen_layer_b_blocker.md"
    if layer_b_metrics.exists():
        status = PASS
        detail = "Layer-B 主实验已有真实训练指标。"
    elif qwen_blocker.exists():
        status = PARTIAL
        detail = "当前环境无GPU，已输出 blocker，流程可继续但主实验结果待算力补齐。"
    else:
        status = FAIL
        detail = "既无 Layer-B 指标也无 blocker，流程状态不可审计。"
    results.append(
        CheckResult(
            id="A10",
            requirement="完整规模实验可行性与阻塞可审计",
            status=status,
            detail=detail,
            evidence=["reports/small_real/qwen_layer_b_blocker.md", "reports/training/layer_b_qwen25_7b_sft_metrics.json"],
            source_refs=["【PDF | 页码p13 | 段落#1】", "【DOCX | 方法与实验设计 | 段落#1】"],
        )
    )

    # A11: task audit consistency.
    task_audit = load_json(root / "reports/task_audit.json")
    done_missing = None
    if task_audit and isinstance(task_audit, dict):
        done_missing = int(task_audit.get("summary", {}).get("done_missing", -1))
    if done_missing == 0:
        status = PASS
        detail = "任务审计显示 DONE 项交付物完整。"
    elif done_missing is None or done_missing < 0:
        status = PARTIAL
        detail = "缺少 task_audit 数据，建议先运行 task completion audit。"
    else:
        status = PARTIAL
        detail = f"任务审计存在 DONE 缺失项: {done_missing}。"
    results.append(
        CheckResult(
            id="A11",
            requirement="任务清单与交付物一致性",
            status=status,
            detail=detail,
            evidence=["reports/task_audit.json", "reports/task_audit.md"],
            source_refs=["【DOCX | 题目与任务定义 | 段落#1】"],
        )
    )

    summary = {
        "total": len(results),
        "pass": sum(1 for x in results if x.status == PASS),
        "partial": sum(1 for x in results if x.status == PARTIAL),
        "fail": sum(1 for x in results if x.status == FAIL),
    }

    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "summary": summary,
                "checks": [x.__dict__ for x in results],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 开题一致性审计报告",
        "",
        f"- PASS: {summary['pass']}",
        f"- PARTIAL: {summary['partial']}",
        f"- FAIL: {summary['fail']}",
        "",
        "| ID | 要求 | 状态 | 结论 | 关键证据 | 开题引用 |",
        "|---|---|---|---|---|---|",
    ]
    for item in results:
        lines.append(
            f"| {item.id} | {item.requirement} | {item.status} | {item.detail} | "
            f"{'<br>'.join(item.evidence)} | {'<br>'.join(item.source_refs)} |"
        )

    out_md = root / args.out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
