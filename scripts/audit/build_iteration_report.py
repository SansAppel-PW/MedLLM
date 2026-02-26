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
    qwen_blocked = Path(args.qwen_blocker).exists()
    baseline_ready = Path(args.baseline_table).exists()

    risk_items = [
        {
            "type": "技术风险",
            "level": "中",
            "summary": "对齐训练（DPO/SimPO/KTO）仍以代理流程为主，真实对齐未完成。",
            "mitigation": "保留脚本接口并优先推进 Qwen7B Layer-B SFT 真实训练后再接真实偏好训练。",
        },
        {
            "type": "算力风险",
            "level": "高" if qwen_blocked else "中",
            "summary": "当前环境是否具备 CUDA 决定 Qwen7B 主实验能否执行。",
            "mitigation": "使用 run_layer_b_qwen_autofallback.sh；无 GPU 输出 blocker，有 GPU 自动 OOM 回退。",
        },
        {
            "type": "数据风险",
            "level": "中",
            "summary": "small-real 当前样本规模小，不能用于论文主结论。",
            "mitigation": "迁移到 real_* 数据并扩容后再产出主结果表与消融。",
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
            "answer": "是，已产出 loss 曲线、eval 指标、run card、baseline 审计表。",
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
        "risk_assessment": risk_items,
        "paper_contribution": contribution,
        "next_min_loop": [
            "在 GPU 环境运行 Qwen7B Layer-B 自动回退训练脚本并产出真实 loss/ckpt/eval。",
            "补齐真实 DPO/SimPO 训练入口并执行至少 1 组消融。",
            "更新 baseline 对比表为“真实主结果 + 代理背景”双层表述。",
        ],
    }

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
