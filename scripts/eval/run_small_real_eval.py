#!/usr/bin/env python3
"""Offline evaluation for small real-training checkpoints."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import torch
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text: str) -> str:
    return "".join(str(text).strip().split())


def lcs_len(a: str, b: str) -> int:
    if not a or not b:
        return 0
    n, m = len(a), len(b)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev = 0
        for j in range(1, m + 1):
            cur = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = cur
    return dp[m]


def rouge_l_f1(pred: str, ref: str) -> float:
    pred = normalize_text(pred)
    ref = normalize_text(ref)
    if not pred or not ref:
        return 0.0
    lcs = lcs_len(pred, ref)
    p = lcs / len(pred)
    r = lcs / len(ref)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def char_f1(pred: str, ref: str) -> float:
    pred = normalize_text(pred)
    ref = normalize_text(ref)
    if not pred or not ref:
        return 0.0
    pred_set = list(pred)
    ref_set = list(ref)
    overlap = 0
    ref_pool = ref_set[:]
    for ch in pred_set:
        if ch in ref_pool:
            overlap += 1
            ref_pool.remove(ch)
    p = overlap / len(pred_set) if pred_set else 0.0
    r = overlap / len(ref_set) if ref_set else 0.0
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def format_prompt(row: dict[str, Any]) -> str:
    query = str(row.get("query", "")).strip()
    context = str(row.get("context", "")).strip()
    if context:
        query = f"{query}\n\n上下文:\n{context}"
    return f"User: {query}\nAssistant:"


def load_model(model_dir: Path) -> tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(
        str(model_dir),
        trust_remote_code=False,
        local_files_only=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    adapter_cfg = model_dir / "adapter_config.json"
    if adapter_cfg.exists():
        peft_cfg = PeftConfig.from_pretrained(str(model_dir), local_files_only=True)
        base = AutoModelForCausalLM.from_pretrained(
            peft_cfg.base_model_name_or_path,
            trust_remote_code=False,
            local_files_only=True,
        )
        model = PeftModel.from_pretrained(base, str(model_dir), local_files_only=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            str(model_dir),
            trust_remote_code=False,
            local_files_only=True,
        )
    model.eval()
    return model, tokenizer


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate small real-training checkpoint")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--input", default="data/clean/sft_dev.jsonl")
    parser.add_argument("--pred-out", default="reports/small_real/predictions.jsonl")
    parser.add_argument("--metrics-json", default="reports/small_real/eval_metrics.json")
    parser.add_argument("--metrics-csv", default="reports/small_real/eval_metrics.csv")
    parser.add_argument("--report-md", default="reports/small_real/eval_report.md")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    rows = load_jsonl(Path(args.input))
    model, tokenizer = load_model(model_dir)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    predictions: list[dict[str, Any]] = []
    em_sum = 0.0
    rouge_sum = 0.0
    f1_sum = 0.0

    for row in rows:
        prompt = format_prompt(row)
        encoded = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(
                **encoded,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id,
            )
        gen_ids = out[0][encoded["input_ids"].shape[1] :]
        pred = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
        ref = str(row.get("answer", "")).strip()
        em = 1.0 if normalize_text(pred) == normalize_text(ref) and ref else 0.0
        rouge = rouge_l_f1(pred, ref)
        f1 = char_f1(pred, ref)

        em_sum += em
        rouge_sum += rouge
        f1_sum += f1

        predictions.append(
            {
                "id": row.get("id"),
                "query": row.get("query"),
                "reference": ref,
                "prediction": pred,
                "exact_match": em,
                "rouge_l_f1": round(rouge, 6),
                "char_f1": round(f1, 6),
            }
        )

    n = max(len(rows), 1)
    metrics = {
        "samples": len(rows),
        "exact_match": em_sum / n,
        "rouge_l_f1": rouge_sum / n,
        "char_f1": f1_sum / n,
        "model_dir": str(model_dir),
        "input": args.input,
        "device": str(device),
    }

    save_jsonl(Path(args.pred_out), predictions)
    Path(args.metrics_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.metrics_json).write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    Path(args.metrics_csv).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.metrics_csv).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["samples", "exact_match", "rouge_l_f1", "char_f1", "device"])
        writer.writeheader()
        writer.writerow(
            {
                "samples": metrics["samples"],
                "exact_match": f"{metrics['exact_match']:.6f}",
                "rouge_l_f1": f"{metrics['rouge_l_f1']:.6f}",
                "char_f1": f"{metrics['char_f1']:.6f}",
                "device": metrics["device"],
            }
        )

    report_lines = [
        "# Small Real Eval Report",
        "",
        f"- model_dir: `{metrics['model_dir']}`",
        f"- input: `{metrics['input']}`",
        f"- samples: {metrics['samples']}",
        f"- exact_match: {metrics['exact_match']:.6f}",
        f"- rouge_l_f1: {metrics['rouge_l_f1']:.6f}",
        f"- char_f1: {metrics['char_f1']:.6f}",
        "",
        "## Artifacts",
        f"- predictions: `{args.pred_out}`",
        f"- metrics_json: `{args.metrics_json}`",
        f"- metrics_csv: `{args.metrics_csv}`",
    ]
    Path(args.report_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report_md).write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps(metrics, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
