#!/usr/bin/env python3
"""Real preference alignment trainer (DPO/SimPO/KTO style)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


try:
    from .utils import load_jsonl, save_json
except ImportError:  # pragma: no cover
    from utils import load_jsonl, save_json


def str2bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "t", "yes", "y"}:
        return True
    if lowered in {"0", "false", "f", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid bool value: {value}")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def git_commit_hash() -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        return None
    return out.decode("utf-8").strip() or None


def parse_target_modules(raw: str) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def cuda_supports_bf16(torch_mod: Any) -> bool:
    if not torch_mod.cuda.is_available():
        return False
    for i in range(torch_mod.cuda.device_count()):
        major, _minor = torch_mod.cuda.get_device_capability(i)
        if int(major) < 8:
            return False
    return True


def import_training_stack() -> dict[str, Any]:
    missing: list[str] = []

    try:
        import torch
    except ModuleNotFoundError:
        missing.append("torch")
        torch = None  # type: ignore

    try:
        import torch.nn.functional as F
    except ModuleNotFoundError:
        missing.append("torch")
        F = None  # type: ignore

    try:
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    except ModuleNotFoundError:
        missing.append("peft")
        LoraConfig = get_peft_model = prepare_model_for_kbit_training = None  # type: ignore

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, get_scheduler, set_seed
    except ModuleNotFoundError:
        missing.append("transformers")
        AutoModelForCausalLM = AutoTokenizer = BitsAndBytesConfig = get_scheduler = set_seed = None  # type: ignore

    if missing:
        need = ", ".join(sorted(set(missing)))
        raise ModuleNotFoundError(
            "Missing dependencies for real preference training: "
            f"{need}. Install with `python -m pip install -r requirements.txt`."
        )

    return {
        "torch": torch,
        "F": F,
        "LoraConfig": LoraConfig,
        "get_peft_model": get_peft_model,
        "prepare_model_for_kbit_training": prepare_model_for_kbit_training,
        "AutoModelForCausalLM": AutoModelForCausalLM,
        "AutoTokenizer": AutoTokenizer,
        "BitsAndBytesConfig": BitsAndBytesConfig,
        "get_scheduler": get_scheduler,
        "set_seed": set_seed,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Real preference trainer")
    parser.add_argument("--pref-file", default="data/clean/real_pref_seed_pairs.jsonl")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--output-dir", default="checkpoints/dpo-real-baseline")
    parser.add_argument("--logging-dir", default="logs/dpo-real-baseline")
    parser.add_argument("--metrics-out", default="reports/training/dpo_metrics.json")
    parser.add_argument("--method", choices=["dpo", "simpo", "kto"], default="dpo")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--max-pairs", type=int, default=0)
    parser.add_argument("--learning-rate", type=float, default=1e-6)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--gradient-checkpointing", type=str2bool, default=True)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--save-total-limit", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--target-margin", type=float, default=0.5)
    parser.add_argument("--bf16", type=str2bool, default=True)
    parser.add_argument("--fp16", type=str2bool, default=False)
    parser.add_argument("--device-map-auto", type=str2bool, default=True)
    parser.add_argument("--trust-remote-code", type=str2bool, default=True)
    parser.add_argument("--use-lora", type=str2bool, default=True)
    parser.add_argument("--lora-r", type=int, default=32)
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument(
        "--lora-target-modules",
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
    )
    parser.add_argument("--load-in-4bit", type=str2bool, default=True)
    parser.add_argument("--bnb-4bit-quant-type", default="nf4")
    parser.add_argument("--bnb-4bit-use-double-quant", type=str2bool, default=True)
    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="real_pref")
    return parser


@dataclass
class PrefExample:
    pair_id: str
    prompt: str
    chosen: str
    rejected: str


def format_chat(tokenizer: Any, prompt: str, answer: str) -> str:
    messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": answer},
    ]
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        except Exception:  # noqa: BLE001
            pass
    return f"User: {prompt}\nAssistant: {answer}"


class PreferenceDataset:
    def __init__(self, examples: list[PrefExample], tokenizer: Any, max_length: int):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        ex = self.examples[idx]
        chosen_text = format_chat(self.tokenizer, ex.prompt, ex.chosen)
        rejected_text = format_chat(self.tokenizer, ex.prompt, ex.rejected)
        chosen_tokens = self.tokenizer(
            chosen_text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        rejected_tokens = self.tokenizer(
            rejected_text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )
        return {
            "pair_id": ex.pair_id,
            "chosen_input_ids": chosen_tokens["input_ids"],
            "chosen_attention_mask": chosen_tokens["attention_mask"],
            "rejected_input_ids": rejected_tokens["input_ids"],
            "rejected_attention_mask": rejected_tokens["attention_mask"],
        }


def make_collate_fn(tokenizer: Any):
    def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
        chosen = tokenizer.pad(
            {
                "input_ids": [x["chosen_input_ids"] for x in batch],
                "attention_mask": [x["chosen_attention_mask"] for x in batch],
            },
            padding=True,
            return_tensors="pt",
        )
        rejected = tokenizer.pad(
            {
                "input_ids": [x["rejected_input_ids"] for x in batch],
                "attention_mask": [x["rejected_attention_mask"] for x in batch],
            },
            padding=True,
            return_tensors="pt",
        )
        return {
            "pair_id": [x["pair_id"] for x in batch],
            "chosen_input_ids": chosen["input_ids"],
            "chosen_attention_mask": chosen["attention_mask"],
            "rejected_input_ids": rejected["input_ids"],
            "rejected_attention_mask": rejected["attention_mask"],
        }

    return collate


def sequence_log_prob(model: Any, F: Any, input_ids: Any, attention_mask: Any) -> Any:
    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    logits = outputs.logits[:, :-1, :]
    labels = input_ids[:, 1:]
    mask = attention_mask[:, 1:]
    log_probs = F.log_softmax(logits, dim=-1)
    token_log_probs = log_probs.gather(dim=-1, index=labels.unsqueeze(-1)).squeeze(-1)
    denom = mask.sum(dim=1).clamp(min=1)
    return (token_log_probs * mask).sum(dim=1) / denom


def ensure_keep_recent_checkpoints(base_dir: Path, keep_last: int) -> None:
    if keep_last <= 0:
        return
    checkpoints = []
    for p in base_dir.glob("checkpoint-*"):
        try:
            step = int(p.name.split("-")[-1])
        except ValueError:
            continue
        checkpoints.append((step, p))
    checkpoints.sort(key=lambda x: x[0])
    stale = checkpoints[:-keep_last]
    for _, path in stale:
        shutil.rmtree(path, ignore_errors=True)


def save_checkpoint(model: Any, tokenizer: Any, output_dir: Path, step: int, keep_last: int) -> None:
    ckpt = output_dir / f"checkpoint-{step}"
    ckpt.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(ckpt))
    tokenizer.save_pretrained(str(ckpt))
    ensure_keep_recent_checkpoints(output_dir, keep_last=keep_last)


def main() -> int:
    args = build_parser().parse_args()
    stack = import_training_stack()
    torch = stack["torch"]
    F = stack["F"]
    LoraConfig = stack["LoraConfig"]
    get_peft_model = stack["get_peft_model"]
    prepare_model_for_kbit_training = stack["prepare_model_for_kbit_training"]
    AutoModelForCausalLM = stack["AutoModelForCausalLM"]
    AutoTokenizer = stack["AutoTokenizer"]
    BitsAndBytesConfig = stack["BitsAndBytesConfig"]
    get_scheduler = stack["get_scheduler"]
    set_seed = stack["set_seed"]

    pref_path = Path(args.pref_file)
    if not pref_path.exists():
        raise FileNotFoundError(f"Preference file not found: {pref_path}")

    output_dir = Path(args.output_dir)
    logging_dir = Path(args.logging_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logging_dir.mkdir(parents=True, exist_ok=True)
    log_jsonl = logging_dir / "train_log.jsonl"

    random.seed(args.seed)
    set_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    raw_pairs = load_jsonl(pref_path)
    examples: list[PrefExample] = []
    for row in raw_pairs:
        prompt = str(row.get("prompt", "")).strip()
        chosen = str(row.get("chosen", "")).strip()
        rejected = str(row.get("rejected", "")).strip()
        if not prompt or not chosen or not rejected:
            continue
        examples.append(
            PrefExample(
                pair_id=str(row.get("id", f"pair_{len(examples)}")),
                prompt=prompt,
                chosen=chosen,
                rejected=rejected,
            )
        )
    if args.max_pairs > 0 and len(examples) > args.max_pairs:
        examples = examples[: args.max_pairs]

    if not examples:
        raise ValueError("No valid preference examples found.")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=args.trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    if not torch.cuda.is_available():
        if args.load_in_4bit:
            print("[warn] CUDA not available, disable 4-bit loading automatically.")
            args.load_in_4bit = False
        if args.bf16 or args.fp16:
            args.bf16 = False
            args.fp16 = False
    elif args.bf16 and not cuda_supports_bf16(torch):
        print("[warn] bf16 is not supported on current CUDA devices; fallback to fp16.")
        args.bf16 = False
        if not args.fp16:
            args.fp16 = True

    quantization_config = None
    load_kwargs: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    if args.device_map_auto:
        load_kwargs["device_map"] = "auto"

    if args.load_in_4bit:
        compute_dtype = torch.bfloat16 if args.bf16 else torch.float16
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=args.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=args.bnb_4bit_use_double_quant,
            bnb_4bit_compute_dtype=compute_dtype,
        )
        load_kwargs["quantization_config"] = quantization_config
    else:
        if args.bf16:
            load_kwargs["torch_dtype"] = torch.bfloat16
        elif args.fp16:
            load_kwargs["torch_dtype"] = torch.float16

    model = AutoModelForCausalLM.from_pretrained(args.model_name, **load_kwargs)
    if args.load_in_4bit:
        model = prepare_model_for_kbit_training(model)
    if args.gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
        if hasattr(model, "enable_input_require_grads"):
            model.enable_input_require_grads()

    if args.use_lora:
        targets = parse_target_modules(args.lora_target_modules)
        lora_cfg = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=targets,
            task_type="CAUSAL_LM",
            bias="none",
        )
        model = get_peft_model(model, lora_cfg)
        model.print_trainable_parameters()

    dataset = PreferenceDataset(examples=examples, tokenizer=tokenizer, max_length=args.max_length)
    collate_fn = make_collate_fn(tokenizer)
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=args.per_device_train_batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_fn,
    )

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    total_batches = len(loader) * max(1, int(args.num_train_epochs))
    total_update_steps = max(1, total_batches // max(args.gradient_accumulation_steps, 1))
    if args.max_steps > 0:
        total_update_steps = min(total_update_steps, args.max_steps)
    warmup_steps = int(total_update_steps * max(args.warmup_ratio, 0.0))
    scheduler = get_scheduler(
        name=args.lr_scheduler_type,
        optimizer=optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=max(total_update_steps, 1),
    )

    manifest = {
        "task": args.task,
        "created_at_utc": now_utc(),
        "command": " ".join(shlex.quote(x) for x in sys.argv),
        "cwd": str(Path.cwd()),
        "git_commit": git_commit_hash(),
        "method": args.method,
        "model_name": args.model_name,
        "seed": args.seed,
        "config": args.config or None,
        "pref_file": str(pref_path),
        "pref_file_sha256": sha256_of_file(pref_path),
        "pairs": len(examples),
        "output_dir": str(output_dir),
        "logging_dir": str(logging_dir),
        "hostname": os.uname().nodename if hasattr(os, "uname") else None,
    }
    save_json(output_dir / "run_manifest.json", manifest)
    if args.config:
        cfg_path = Path(args.config)
        if cfg_path.exists():
            shutil.copy2(cfg_path, output_dir / "config_snapshot.yaml")

    try:
        model.train()
        optimizer.zero_grad(set_to_none=True)
        global_step = 0
        grad_step = 0
        loss_total = 0.0
        delta_total = 0.0
        delta_count = 0
        stop = False

        device = next(model.parameters()).device

        for epoch in range(max(1, int(args.num_train_epochs))):
            if stop:
                break
            for batch in loader:
                chosen_input_ids = batch["chosen_input_ids"].to(device)
                chosen_attention_mask = batch["chosen_attention_mask"].to(device)
                rejected_input_ids = batch["rejected_input_ids"].to(device)
                rejected_attention_mask = batch["rejected_attention_mask"].to(device)

                chosen_logp = sequence_log_prob(
                    model=model,
                    F=F,
                    input_ids=chosen_input_ids,
                    attention_mask=chosen_attention_mask,
                )
                rejected_logp = sequence_log_prob(
                    model=model,
                    F=F,
                    input_ids=rejected_input_ids,
                    attention_mask=rejected_attention_mask,
                )
                delta = chosen_logp - rejected_logp
                beta = float(args.beta)
                if args.method == "dpo":
                    batch_loss = -F.logsigmoid(beta * delta).mean()
                elif args.method == "simpo":
                    batch_loss = -F.logsigmoid(beta * (delta - float(args.target_margin))).mean()
                else:  # kto
                    batch_loss = -0.5 * (
                        F.logsigmoid(beta * chosen_logp).mean() + F.logsigmoid(-beta * rejected_logp).mean()
                    )

                (batch_loss / args.gradient_accumulation_steps).backward()
                grad_step += 1
                loss_total += float(batch_loss.detach().item())
                delta_total += float(delta.detach().mean().item())
                delta_count += 1

                if grad_step % args.gradient_accumulation_steps != 0:
                    continue

                if args.max_grad_norm > 0:
                    torch.nn.utils.clip_grad_norm_(trainable_params, args.max_grad_norm)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1

                if global_step % args.logging_steps == 0:
                    log_row = {
                        "time_utc": now_utc(),
                        "step": global_step,
                        "epoch": epoch + 1,
                        "loss": float(batch_loss.detach().item()),
                        "avg_delta": delta_total / max(delta_count, 1),
                        "lr": float(scheduler.get_last_lr()[0]),
                    }
                    with log_jsonl.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(log_row, ensure_ascii=False) + "\n")
                    print(
                        f"[real-{args.method}] step={global_step} "
                        f"loss={log_row['loss']:.6f} delta={log_row['avg_delta']:.6f}"
                    )

                if global_step % args.save_steps == 0:
                    save_checkpoint(
                        model=model,
                        tokenizer=tokenizer,
                        output_dir=output_dir,
                        step=global_step,
                        keep_last=args.save_total_limit,
                    )

                if args.max_steps > 0 and global_step >= args.max_steps:
                    stop = True
                    break

        final_dir = output_dir / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(final_dir))
        tokenizer.save_pretrained(str(final_dir))
        ensure_keep_recent_checkpoints(output_dir, keep_last=args.save_total_limit)

        metrics = {
            "method": args.method.upper(),
            "task": args.task,
            "simulation": False,
            "samples": len(examples),
            "global_steps": global_step,
            "avg_loss": loss_total / max(delta_count, 1),
            "avg_delta": delta_total / max(delta_count, 1),
            "beta": args.beta,
            "target_margin": args.target_margin if args.method == "simpo" else None,
            "created_at_utc": now_utc(),
            "config": args.config or None,
            "model_name": args.model_name,
            "save_total_limit": args.save_total_limit,
        }
        aligned_score = 1.0 / (1.0 + math.exp(-float(metrics["avg_delta"])))
        metrics["base_score"] = 0.5
        metrics["aligned_score"] = aligned_score
        metrics["score_gain"] = aligned_score - float(metrics["base_score"])
        save_json(output_dir / "metrics.json", metrics)
        save_json(args.metrics_out, metrics)
        print(
            f"[real-{args.method}] samples={len(examples)} "
            f"steps={global_step} output={output_dir} metrics={args.metrics_out}"
        )
        return 0
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            print("[real-pref] CUDA OOM detected.")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
