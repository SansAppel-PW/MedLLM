#!/usr/bin/env python3
"""Build a structured iteration report for paper-oriented autonomous loops."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_load_json(path: Path) -> dict[str, Any] | None:
    if path.exists():
        return load_json(path)
    return None


def alignment_metric(metrics: dict[str, Any] | None) -> float | None:
    if not metrics:
        return None
    for key in ("pref_accuracy_after", "aligned_score"):
        value = metrics.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def baseline_layer_counts(payload: dict[str, Any] | list[Any] | None) -> tuple[int | None, int | None]:
    if payload is None:
        return None, None
    if isinstance(payload, dict):
        real_rows = payload.get("real_mainline")
        proxy_rows = payload.get("proxy_background")
        if isinstance(real_rows, list) and isinstance(proxy_rows, list):
            return len(real_rows), len(proxy_rows)
        all_rows = payload.get("all")
        if isinstance(all_rows, list):
            real = 0
            proxy = 0
            for row in all_rows:
                if not isinstance(row, dict):
                    continue
                layer = row.get("evidence_layer")
                if layer == "real-mainline":
                    real += 1
                elif layer == "proxy-background":
                    proxy += 1
            return real, proxy
    if isinstance(payload, list):
        real = 0
        proxy = 0
        for row in payload:
            if not isinstance(row, dict):
                continue
            layer = row.get("evidence_layer")
            if layer == "real-mainline":
                real += 1
            elif layer == "proxy-background":
                proxy += 1
        return real, proxy
    return None, None


def resolve_small_real_paths(run_tag: str | None) -> tuple[str, str]:
    if run_tag:
        train = Path(f"reports/training/{run_tag}_metrics.json")
        eval_metrics = Path(f"reports/small_real/{run_tag}/eval_metrics.json")
        return str(train), str(eval_metrics)

    base = Path("reports/small_real")
    candidates = [p for p in base.glob("small_real_lora_v*/") if (p / "eval_metrics.json").exists()]
    if candidates:
        latest_dir = max(candidates, key=lambda p: (p / "eval_metrics.json").stat().st_mtime)
        latest_tag = latest_dir.name
        return f"reports/training/{latest_tag}_metrics.json", str(latest_dir / "eval_metrics.json")
    return "reports/training/small_real_lora_v3_metrics.json", "reports/small_real/small_real_lora_v3/eval_metrics.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build autonomous iteration report")
    parser.add_argument("--title", default="Loop Iteration Report")
    parser.add_argument("--run-tag", default=os.getenv("RUN_TAG"), help="Optional small-real run tag")
    parser.add_argument("--small-real-metrics", default=None)
    parser.add_argument("--small-real-eval", default=None)
    parser.add_argument("--baseline-json", default="reports/thesis_assets/tables/baseline_audit_table.json")
    parser.add_argument("--real-dataset-summary", default="reports/real_dataset_summary.json")
    parser.add_argument("--dpo-real-metrics", default="reports/training/dpo_real_metrics.json")
    parser.add_argument("--simpo-metrics", default="reports/training/simpo_metrics.json")
    parser.add_argument("--kto-metrics", default="reports/training/kto_metrics.json")
    parser.add_argument("--qwen-blocker", default="reports/small_real/qwen_layer_b_blocker.md")
    parser.add_argument("--baseline-table", default="reports/thesis_assets/tables/baseline_audit_table.csv")
    parser.add_argument("--out-md", default="reports/iteration/latest_iteration_report.md")
    parser.add_argument("--out-json", default="reports/iteration/latest_iteration_report.json")
    args = parser.parse_args()

    default_train, default_eval = resolve_small_real_paths(args.run_tag)
    small_real_metrics_path = args.small_real_metrics or default_train
    small_real_eval_path = args.small_real_eval or default_eval

    now_utc = datetime.now(timezone.utc).isoformat()
    small_train = maybe_load_json(Path(small_real_metrics_path))
    small_eval = maybe_load_json(Path(small_real_eval_path))
    real_data = maybe_load_json(Path(args.real_dataset_summary))
    baseline_payload = maybe_load_json(Path(args.baseline_json))
    dpo_real = maybe_load_json(Path(args.dpo_real_metrics))
    simpo_metrics = maybe_load_json(Path(args.simpo_metrics))
    kto_metrics = maybe_load_json(Path(args.kto_metrics))
    qwen_blocked = Path(args.qwen_blocker).exists()
    baseline_ready = Path(args.baseline_table).exists()

    real_train_count = int(real_data.get("train_count", 0)) if real_data else 0
    real_dev_count = int(real_data.get("dev_count", 0)) if real_data else 0
    real_test_count = int(real_data.get("test_count", 0)) if real_data else 0
    baseline_real_count, baseline_proxy_count = baseline_layer_counts(baseline_payload)
    simpo_real = bool(simpo_metrics and simpo_metrics.get("simulation") is False)
    kto_real = bool(kto_metrics and kto_metrics.get("simulation") is False)

    alignment_rows = []
    for method, payload in (("DPO", dpo_real), ("SimPO", simpo_metrics), ("KTO", kto_metrics)):
        score = alignment_metric(payload)
        if score is None:
            continue
        alignment_rows.append({"method": method, "score": score})
    best_alignment = max(alignment_rows, key=lambda x: x["score"]) if alignment_rows else None

    if dpo_real and simpo_real and kto_real:
        technical_risk = {
            "type": "技术风险",
            "level": "低",
            "summary": "对齐训练已覆盖真实 DPO/SimPO/KTO，闭环完整。",
            "mitigation": "保持控制变量法迭代并扩充偏好数据规模，巩固统计显著性。",
        }
    elif dpo_real:
        technical_risk = {
            "type": "技术风险",
            "level": "中",
            "summary": "对齐训练已支持真实 DPO，但 SimPO/KTO 仍为代理流程。",
            "mitigation": "保持真实 DPO 持续迭代，并在后续阶段补齐 SimPO/KTO 真实训练入口。",
        }
    else:
        technical_risk = {
            "type": "技术风险",
            "level": "中",
            "summary": "对齐训练（DPO/SimPO/KTO）仍以代理流程为主，真实对齐未完成。",
            "mitigation": "保留脚本接口并优先推进 Qwen7B Layer-B SFT 真实训练后再接真实偏好训练。",
        }

    data_risk_level = "中"
    data_risk_summary = "small-real 当前样本规模小，不能用于论文主结论。"
    data_mitigation = "迁移到 real_* 数据并扩容后再产出主结果表与消融。"
    if real_train_count >= 200 and real_dev_count > 0 and real_test_count > 0:
        data_risk_level = "低"
        data_risk_summary = "real_* 数据集已构建且可用于真实训练与评测。"
        data_mitigation = "继续提升数据规模与多源覆盖，并记录许可与偏差分析。"

    risk_items = [
        technical_risk,
        {
            "type": "算力风险",
            "level": "高" if qwen_blocked else "中",
            "summary": "当前环境是否具备 CUDA 决定 Qwen7B 主实验能否执行。",
            "mitigation": "使用 run_layer_b_qwen_autofallback.sh；无 GPU 输出 blocker，有 GPU 自动 OOM 回退。",
        },
        {
            "type": "数据风险",
            "level": data_risk_level,
            "summary": data_risk_summary,
            "mitigation": data_mitigation,
        },
        {
            "type": "论文逻辑风险",
            "level": "中",
            "summary": "proxy 与 real 结果混写会导致证据链不可信。",
            "mitigation": "继续保持分层目录与报告口径隔离。",
        },
    ]

    contribution = [
        {
            "question": "对应论文哪个章节/小节？",
            "answer": "第3章实验系统、第5章训练流程、第6章阶段性结果与风险。",
        },
        {
            "question": "是否产出论文可用图表/数据/表格？",
            "answer": "是，已产出 loss 曲线、eval 指标、run card、baseline 审计表，并补充 real alignment 指标。",
        },
        {
            "question": "是否增强创新性或严谨性？体现在哪里？",
            "answer": "主要增强严谨性：真实闭环证据链 + 自动回退 + blocker 可审计机制。",
        },
        {
            "question": "若不服务论文，是否降级为附录？",
            "answer": "small-real fallback 结果降级为附录/工程验证，不作为主结论。",
        },
    ]

    payload = {
        "title": args.title,
        "generated_at_utc": now_utc,
        "run_tag": args.run_tag,
        "artifacts": {
            "small_real_train_metrics": small_real_metrics_path,
            "small_real_eval_metrics": small_real_eval_path,
            "baseline_json": args.baseline_json if baseline_payload else None,
            "real_dataset_summary": args.real_dataset_summary if real_data else None,
            "dpo_real_metrics": args.dpo_real_metrics if dpo_real else None,
            "simpo_metrics": args.simpo_metrics if simpo_metrics else None,
            "kto_metrics": args.kto_metrics if kto_metrics else None,
            "qwen_blocker": args.qwen_blocker if qwen_blocked else None,
            "baseline_table": args.baseline_table if baseline_ready else None,
        },
        "small_real_summary": {
            "train_loss": small_train.get("train_loss") if small_train else None,
            "final_eval_loss": small_train.get("final_eval_loss") if small_train else None,
            "exact_match": small_eval.get("exact_match") if small_eval else None,
            "rouge_l_f1": small_eval.get("rouge_l_f1") if small_eval else None,
            "char_f1": small_eval.get("char_f1") if small_eval else None,
        },
        "real_data_summary": {
            "train_count": real_train_count if real_data else None,
            "dev_count": real_dev_count if real_data else None,
            "test_count": real_test_count if real_data else None,
            "benchmark_count": int(real_data.get("benchmark_count", 0)) if real_data else None,
        },
        "real_alignment_summary": {
            "dpo_pair_count": int(dpo_real.get("pair_count", 0)) if dpo_real else None,
            "dpo_pref_accuracy_after": alignment_metric(dpo_real),
            "simpo_score_after": alignment_metric(simpo_metrics),
            "kto_score_after": alignment_metric(kto_metrics),
            "best_method": best_alignment["method"] if best_alignment else None,
            "best_score": best_alignment["score"] if best_alignment else None,
        },
        "baseline_layer_summary": {
            "real_mainline_count": baseline_real_count,
            "proxy_background_count": baseline_proxy_count,
        },
        "risk_assessment": risk_items,
        "paper_contribution": contribution,
        "next_min_loop": [],
    }

    next_steps = payload["next_min_loop"]
    if qwen_blocked:
        next_steps.append("在 GPU 环境运行 Qwen7B Layer-B 自动回退训练脚本并产出真实 loss/ckpt/eval。")
    else:
        next_steps.append("在当前可用算力上补跑 Qwen7B Layer-B 消融，更新主结果表。")

    if not dpo_real:
        next_steps.append("补齐真实 DPO 训练闭环并导出可复现 metrics/run manifest。")
    else:
        next_steps.append("保持真实 DPO，继续扩容偏好对并执行至少 1 组 real-alignment 消融。")

    next_steps.append("更新 baseline 对比表为“真实主结果 + 代理背景”双层表述。")

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        f"# {args.title}",
        "",
        f"- 生成时间(UTC): {now_utc}",
        "",
        "## 关键结果摘要",
        f"- train_loss: {payload['small_real_summary']['train_loss']}",
        f"- final_eval_loss: {payload['small_real_summary']['final_eval_loss']}",
        f"- exact_match: {payload['small_real_summary']['exact_match']}",
        f"- rouge_l_f1: {payload['small_real_summary']['rouge_l_f1']}",
        f"- char_f1: {payload['small_real_summary']['char_f1']}",
        "",
        "## 真实数据摘要",
        f"- real_train_count: {payload['real_data_summary']['train_count']}",
        f"- real_dev_count: {payload['real_data_summary']['dev_count']}",
        f"- real_test_count: {payload['real_data_summary']['test_count']}",
        f"- real_benchmark_count: {payload['real_data_summary']['benchmark_count']}",
        "",
        "## 真实对齐摘要",
        f"- dpo_pair_count: {payload['real_alignment_summary']['dpo_pair_count']}",
        f"- dpo_pref_accuracy_after: {payload['real_alignment_summary']['dpo_pref_accuracy_after']}",
        f"- simpo_score_after: {payload['real_alignment_summary']['simpo_score_after']}",
        f"- kto_score_after: {payload['real_alignment_summary']['kto_score_after']}",
        f"- best_alignment_method: {payload['real_alignment_summary']['best_method']}",
        f"- best_alignment_score: {payload['real_alignment_summary']['best_score']}",
        "",
        "## Baseline 分层摘要",
        f"- baseline_real_mainline_count: {payload['baseline_layer_summary']['real_mainline_count']}",
        f"- baseline_proxy_background_count: {payload['baseline_layer_summary']['proxy_background_count']}",
        "",
        "## 风险评估",
    ]
    for item in risk_items:
        md.append(f"- {item['type']}（{item['level']}）：{item['summary']} 缓解：{item['mitigation']}")
    md.extend(["", "## 论文贡献度评估（四问）"])
    for qa in contribution:
        md.append(f"- {qa['question']} {qa['answer']}")
    md.extend(["", "## 下一步最小闭环"])
    for x in payload["next_min_loop"]:
        md.append(f"- {x}")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"[iteration-report] md={out_md} json={out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
