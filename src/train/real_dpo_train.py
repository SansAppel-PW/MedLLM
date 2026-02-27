#!/usr/bin/env python3
"""Minimal real DPO-style training with reproducibility artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    from .utils import load_jsonl, save_json
except ImportError:  # pragma: no cover
    from utils import load_jsonl, save_json


def str2bool(v: str | bool) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"1", "true", "t", "yes", "y"}:
        return True
    if s in {"0", "false", "f", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid bool value: {v}")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit_hash() -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        return None
    return out.decode("utf-8").strip() or None


def capture_pip_freeze(path: Path) -> str | None:
    try:
        txt = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    except Exception:  # noqa: BLE001
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt, encoding="utf-8")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Real DPO trainer")
    p.add_argument("--pref-file", default="data/clean/pref_seed_pairs.jsonl")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-0.5B-Instruct")
    p.add_argument("--output-dir", default="checkpoints/alignment/small_real_dpo")
    p.add_argument("--logging-dir", default="logs/alignment/small_real_dpo")
    p.add_argument("--metrics-out", default="reports/training/small_real_dpo_metrics.json")
    p.add_argument("--max-length", type=int, default=256)
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--max-steps", type=int, default=40)
    p.add_argument("--learning-rate", type=float, default=1e-5)
    p.add_argument("--weight-decay", type=float, default=0.0)
    p.add_argument("--beta", type=float, default=0.1)
    p.add_argument("--eval-sample-size", type=int, default=512)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trust-remote-code", type=str2bool, default=True)
    p.add_argument("--local-files-only", type=str2bool, default=False)
    p.add_argument("--task", default="small_real_dpo")
    p.add_argument("--config", default="")
    return p


def pick_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def pair_text(prompt: str, response: str) -> tuple[str, str]:
    prefix = f"User: {prompt.strip()}\nAssistant:"
    suffix = f" {response.strip()}"
    return prefix, suffix


def encode_pair(
    tokenizer: Any,
    prompt: str,
    response: str,
    max_length: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    prefix, suffix = pair_text(prompt, response)
    prompt_ids = tokenizer.encode(prefix, add_special_tokens=False)
    resp_ids = tokenizer.encode(suffix, add_special_tokens=False)
    if tokenizer.eos_token_id is not None:
        resp_ids = resp_ids + [int(tokenizer.eos_token_id)]

    input_ids = prompt_ids + resp_ids
    labels = ([-100] * len(prompt_ids)) + resp_ids

    if len(input_ids) > max_length:
        input_ids = input_ids[-max_length:]
        labels = labels[-max_length:]

    input_t = torch.tensor([input_ids], dtype=torch.long, device=device)
    label_t = torch.tensor([labels], dtype=torch.long, device=device)
    return input_t, label_t


def response_logprob(
    model: Any,
    tokenizer: Any,
    prompt: str,
    response: str,
    max_length: int,
    device: torch.device,
) -> torch.Tensor:
    input_ids, labels = encode_pair(tokenizer, prompt, response, max_length=max_length, device=device)
    outputs = model(input_ids=input_ids)
    logits = outputs.logits[:, :-1, :]
    target = labels[:, 1:]
    mask = target != -100
    safe_target = target.masked_fill(~mask, 0)
    token_logp = F.log_softmax(logits, dim=-1).gather(-1, safe_target.unsqueeze(-1)).squeeze(-1)
    token_logp = token_logp * mask
    denom = mask.sum(dim=1).clamp_min(1)
    return token_logp.sum(dim=1) / denom


@torch.no_grad()
def pair_accuracy(
    model: Any,
    tokenizer: Any,
    pairs: list[dict[str, Any]],
    max_length: int,
    device: torch.device,
) -> float:
    if not pairs:
        return 0.0
    model.eval()
    good = 0
    for row in pairs:
        prompt = str(row.get("prompt", "")).strip()
        chosen = str(row.get("chosen", "")).strip()
        rejected = str(row.get("rejected", "")).strip()
        if not prompt or not chosen or not rejected:
            continue
        c_lp = response_logprob(model, tokenizer, prompt, chosen, max_length=max_length, device=device)
        r_lp = response_logprob(model, tokenizer, prompt, rejected, max_length=max_length, device=device)
        if float(c_lp.item()) > float(r_lp.item()):
            good += 1
    return good / max(len(pairs), 1)


def main() -> int:
    args = build_parser().parse_args()

    pref_path = Path(args.pref_file)
    out_dir = Path(args.output_dir)
    log_dir = Path(args.logging_dir)
    metrics_out = Path(args.metrics_out)
    final_dir = out_dir / "final"
    log_file = log_dir / "train_log.jsonl"
    run_manifest = out_dir / "run_manifest.json"

    out_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)

    if not pref_path.exists():
        raise FileNotFoundError(f"Preference file not found: {pref_path}")

    if os.getenv("HF_HUB_OFFLINE") == "1" or os.getenv("TRANSFORMERS_OFFLINE") == "1":
        args.local_files_only = True

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    pairs = load_jsonl(pref_path)
    pairs = [
        x
        for x in pairs
        if str(x.get("prompt", "")).strip()
        and str(x.get("chosen", "")).strip()
        and str(x.get("rejected", "")).strip()
    ]
    if not pairs:
        raise ValueError("No valid preference pairs.")
    eval_pairs = pairs
    if args.eval_sample_size > 0 and len(pairs) > args.eval_sample_size:
        rng = random.Random(args.seed + 11)
        eval_pairs = rng.sample(pairs, args.eval_sample_size)

    device = pick_device()
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        trust_remote_code=args.trust_remote_code,
        local_files_only=args.local_files_only,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        trust_remote_code=args.trust_remote_code,
        local_files_only=args.local_files_only,
    )
    model.to(device)
    model.train()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)

    before_acc = pair_accuracy(model, tokenizer, eval_pairs, max_length=args.max_length, device=device)

    started = time.time()
    global_step = 0
    losses: list[float] = []
    with log_file.open("w", encoding="utf-8") as logf:
        for epoch in range(args.epochs):
            random.shuffle(pairs)
            for row in pairs:
                prompt = str(row["prompt"])
                chosen = str(row["chosen"])
                rejected = str(row["rejected"])

                chosen_lp = response_logprob(model, tokenizer, prompt, chosen, args.max_length, device)
                rejected_lp = response_logprob(model, tokenizer, prompt, rejected, args.max_length, device)
                margin = chosen_lp - rejected_lp
                loss = -F.logsigmoid(args.beta * margin).mean()

                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()

                global_step += 1
                loss_val = float(loss.detach().item())
                losses.append(loss_val)
                rec = {
                    "step": global_step,
                    "epoch": epoch + 1,
                    "loss": loss_val,
                    "chosen_logp": float(chosen_lp.detach().item()),
                    "rejected_logp": float(rejected_lp.detach().item()),
                    "margin": float(margin.detach().item()),
                }
                logf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                if args.max_steps > 0 and global_step >= args.max_steps:
                    break
            if args.max_steps > 0 and global_step >= args.max_steps:
                break

    model.eval()
    after_acc = pair_accuracy(model, tokenizer, eval_pairs, max_length=args.max_length, device=device)
    elapsed = time.time() - started

    model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)

    metrics = {
        "method": "DPO",
        "simulation": False,
        "task": args.task,
        "pair_count": len(pairs),
        "eval_pair_count": len(eval_pairs),
        "steps": global_step,
        "train_runtime_sec": round(elapsed, 4),
        "train_loss": (sum(losses) / len(losses)) if losses else None,
        "pref_accuracy_before": before_acc,
        "pref_accuracy_after": after_acc,
        "pref_accuracy_gain": after_acc - before_acc,
        "model_name": args.model_name,
        "output_dir": str(out_dir),
        "final_model_dir": str(final_dir),
        "log_jsonl": str(log_file),
        "device": str(device),
    }
    save_json(metrics_out, metrics)

    env_snapshot = {
        "python": sys.version.split()[0],
        "torch": getattr(torch, "__version__", None),
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": getattr(torch.version, "cuda", None),
        "mps_available": bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available()),
        "transformers": __import__("transformers").__version__,
    }

    manifest = {
        "task": args.task,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "argv": sys.argv,
        "config": args.config or None,
        "git_commit": git_commit_hash(),
        "data": {
            "pref_file": str(pref_path),
            "pref_file_sha256": sha256_of_file(pref_path),
            "pair_count": len(pairs),
            "eval_pair_count": len(eval_pairs),
        },
        "model": {
            "base_model": args.model_name,
            "trust_remote_code": args.trust_remote_code,
            "local_files_only": args.local_files_only,
        },
        "environment": env_snapshot,
        "pip_freeze": capture_pip_freeze(log_dir / "pip_freeze.txt"),
        "artifacts": {
            "metrics_out": str(metrics_out),
            "log_jsonl": str(log_file),
            "final_model_dir": str(final_dir),
        },
    }
    save_json(run_manifest, manifest)

    print(
        "[real-dpo] "
        f"pairs={len(pairs)} steps={global_step} "
        f"acc_before={before_acc:.4f} acc_after={after_acc:.4f} "
        f"metrics={metrics_out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
