#!/usr/bin/env python3
"""Real SFT training entrypoint with reproducibility artifacts."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
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


def format_user_prompt(row: dict[str, Any]) -> tuple[str, str] | None:
    query = str(row.get("query", "")).strip()
    answer = str(row.get("answer", "")).strip()
    if not query or not answer:
        return None
    context = str(row.get("context", "")).strip()
    if context:
        query = f"{query}\n\n上下文:\n{context}"
    return query, answer


def parse_target_modules(raw: str) -> list[str]:
    out = [x.strip() for x in (raw or "").split(",") if x.strip()]
    return out


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
        from datasets import Dataset
    except ModuleNotFoundError:
        missing.append("datasets")
        Dataset = None  # type: ignore

    try:
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    except ModuleNotFoundError:
        missing.append("peft")
        LoraConfig = get_peft_model = prepare_model_for_kbit_training = None  # type: ignore

    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainerCallback,
            TrainingArguments,
            set_seed,
        )
    except ModuleNotFoundError:
        missing.append("transformers")
        AutoModelForCausalLM = AutoTokenizer = BitsAndBytesConfig = None  # type: ignore
        DataCollatorForLanguageModeling = Trainer = TrainerCallback = None  # type: ignore
        TrainingArguments = set_seed = None  # type: ignore

    if missing:
        need = ", ".join(sorted(set(missing)))
        raise ModuleNotFoundError(
            "Missing dependencies for real training: "
            f"{need}. Install with `python -m pip install -r requirements.txt`."
        )

    return {
        "torch": torch,
        "Dataset": Dataset,
        "LoraConfig": LoraConfig,
        "get_peft_model": get_peft_model,
        "prepare_model_for_kbit_training": prepare_model_for_kbit_training,
        "AutoModelForCausalLM": AutoModelForCausalLM,
        "AutoTokenizer": AutoTokenizer,
        "BitsAndBytesConfig": BitsAndBytesConfig,
        "DataCollatorForLanguageModeling": DataCollatorForLanguageModeling,
        "Trainer": Trainer,
        "TrainerCallback": TrainerCallback,
        "TrainingArguments": TrainingArguments,
        "set_seed": set_seed,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Real SFT trainer")
    parser.add_argument("--train-file", default="data/clean/real_sft_train.jsonl")
    parser.add_argument("--dev-file", default="data/clean/real_sft_dev.jsonl")
    parser.add_argument("--model-name", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--output-dir", default="checkpoints/layer_b/qwen25-7b-sft")
    parser.add_argument("--logging-dir", default="logs/layer_b/qwen25-7b-sft")
    parser.add_argument("--metrics-out", default="")

    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--optim", default="paged_adamw_8bit")

    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--per-device-eval-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--gradient-checkpointing", type=str2bool, default=True)
    parser.add_argument("--num-workers", type=int, default=2)

    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--save-total-limit", type=int, default=2)

    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bf16", type=str2bool, default=True)
    parser.add_argument("--fp16", type=str2bool, default=False)
    parser.add_argument("--device-map-auto", type=str2bool, default=True)
    parser.add_argument("--trust-remote-code", type=str2bool, default=True)

    parser.add_argument("--use-lora", type=str2bool, default=True)
    parser.add_argument("--lora-r", type=int, default=64)
    parser.add_argument("--lora-alpha", type=int, default=128)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument(
        "--lora-target-modules",
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
    )

    parser.add_argument("--load-in-4bit", type=str2bool, default=True)
    parser.add_argument("--bnb-4bit-quant-type", default="nf4")
    parser.add_argument("--bnb-4bit-use-double-quant", type=str2bool, default=True)

    parser.add_argument("--config", default="")
    parser.add_argument("--task", default="real_sft")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    train_path = Path(args.train_file)
    dev_path = Path(args.dev_file)
    out_dir = Path(args.output_dir)
    log_dir = Path(args.logging_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    if not train_path.exists():
        raise FileNotFoundError(f"Train file not found: {train_path}")
    if not dev_path.exists():
        print(f"[warn] dev file not found: {dev_path}, continue without eval")

    stack = import_training_stack()
    torch = stack["torch"]
    Dataset = stack["Dataset"]
    LoraConfig = stack["LoraConfig"]
    get_peft_model = stack["get_peft_model"]
    prepare_model_for_kbit_training = stack["prepare_model_for_kbit_training"]
    AutoModelForCausalLM = stack["AutoModelForCausalLM"]
    AutoTokenizer = stack["AutoTokenizer"]
    BitsAndBytesConfig = stack["BitsAndBytesConfig"]
    DataCollatorForLanguageModeling = stack["DataCollatorForLanguageModeling"]
    Trainer = stack["Trainer"]
    TrainerCallback = stack["TrainerCallback"]
    TrainingArguments = stack["TrainingArguments"]
    set_seed = stack["set_seed"]

    if not torch.cuda.is_available():
        if args.load_in_4bit:
            print("[warn] CUDA not available, disable 4-bit loading automatically.")
            args.load_in_4bit = False
        if args.bf16 or args.fp16:
            print("[warn] CUDA not available, disable mixed precision flags.")
            args.bf16 = False
            args.fp16 = False
    elif args.bf16 and not cuda_supports_bf16(torch):
        print("[warn] bf16 is not supported on current CUDA devices; fallback to fp16.")
        args.bf16 = False
        if not args.fp16:
            args.fp16 = True

    random.seed(args.seed)
    set_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    train_rows = load_jsonl(train_path)
    dev_rows = load_jsonl(dev_path) if dev_path.exists() else []

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name,
        trust_remote_code=args.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    def render_text(row: dict[str, Any]) -> str | None:
        pair = format_user_prompt(row)
        if pair is None:
            return None
        user_prompt, answer = pair
        messages = [
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": answer},
        ]
        if hasattr(tokenizer, "apply_chat_template"):
            try:
                return tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=False,
                )
            except Exception:  # noqa: BLE001
                pass
        return f"User: {user_prompt}\nAssistant: {answer}"

    train_examples = []
    for row in train_rows:
        text = render_text(row)
        if text:
            train_examples.append({"text": text, "id": row.get("id")})

    dev_examples = []
    for row in dev_rows:
        text = render_text(row)
        if text:
            dev_examples.append({"text": text, "id": row.get("id")})

    if not train_examples:
        raise ValueError("No valid training examples after formatting.")

    train_dataset = Dataset.from_list(train_examples)
    dev_dataset = Dataset.from_list(dev_examples) if dev_examples else None

    def tokenize_fn(batch: dict[str, list[Any]]) -> dict[str, Any]:
        encoded = tokenizer(
            batch["text"],
            truncation=True,
            max_length=args.max_length,
            padding=False,
        )
        return encoded

    train_dataset = train_dataset.map(tokenize_fn, batched=True, remove_columns=train_dataset.column_names)
    if dev_dataset is not None:
        dev_dataset = dev_dataset.map(tokenize_fn, batched=True, remove_columns=dev_dataset.column_names)

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

    if args.use_lora:
        targets = parse_target_modules(args.lora_target_modules)
        lora_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            target_modules=targets,
            task_type="CAUSAL_LM",
            bias="none",
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    log_jsonl = log_dir / "train_log.jsonl"

    class JsonlLogCallback(TrainerCallback):
        def on_log(self, _args, state, _control, logs=None, **_kwargs):
            if not logs:
                return
            payload = {
                "time_utc": datetime.now(timezone.utc).isoformat(),
                "step": int(state.global_step),
                "epoch": float(state.epoch) if state.epoch is not None else None,
                **logs,
            }
            with log_jsonl.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    evaluation_strategy = "steps" if dev_dataset is not None else "no"
    load_best_model_at_end = dev_dataset is not None

    training_kwargs: dict[str, Any] = {
        "output_dir": str(out_dir),
        "overwrite_output_dir": False,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "per_device_eval_batch_size": args.per_device_eval_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "warmup_ratio": args.warmup_ratio,
        "lr_scheduler_type": args.lr_scheduler_type,
        "num_train_epochs": args.num_train_epochs,
        "max_steps": args.max_steps,
        "logging_steps": args.logging_steps,
        "save_steps": args.save_steps,
        "eval_steps": args.eval_steps,
        "evaluation_strategy": evaluation_strategy,
        "save_strategy": "steps",
        "save_total_limit": args.save_total_limit,
        "bf16": args.bf16,
        "fp16": args.fp16,
        "gradient_checkpointing": args.gradient_checkpointing,
        "dataloader_num_workers": args.num_workers,
        "report_to": [],
        "optim": args.optim,
        "logging_dir": str(log_dir),
        "seed": args.seed,
        "load_best_model_at_end": load_best_model_at_end,
        "metric_for_best_model": "eval_loss" if load_best_model_at_end else None,
        "greater_is_better": False if load_best_model_at_end else None,
    }
    ta_params = set(inspect.signature(TrainingArguments.__init__).parameters.keys())
    if "evaluation_strategy" not in ta_params and "eval_strategy" in ta_params:
        training_kwargs["eval_strategy"] = training_kwargs.pop("evaluation_strategy")
    filtered_kwargs = {k: v for k, v in training_kwargs.items() if k in ta_params}
    training_args = TrainingArguments(**filtered_kwargs)

    trainer_kwargs: dict[str, Any] = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": dev_dataset,
        "data_collator": data_collator,
        "callbacks": [JsonlLogCallback()],
    }
    trainer_params = set(inspect.signature(Trainer.__init__).parameters.keys())
    if "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer
    elif "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    trainer = Trainer(**{k: v for k, v in trainer_kwargs.items() if k in trainer_params})

    manifest = {
        "task": args.task,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(shlex.quote(x) for x in sys.argv),
        "cwd": str(Path.cwd()),
        "git_commit": git_commit_hash(),
        "model_name": args.model_name,
        "seed": args.seed,
        "config": args.config or None,
        "train_file": str(train_path),
        "train_file_sha256": sha256_of_file(train_path),
        "dev_file": str(dev_path) if dev_path.exists() else None,
        "dev_file_sha256": sha256_of_file(dev_path) if dev_path.exists() else None,
        "train_samples": len(train_examples),
        "dev_samples": len(dev_examples),
        "output_dir": str(out_dir),
        "logging_dir": str(log_dir),
        "hostname": os.uname().nodename if hasattr(os, "uname") else None,
    }
    save_json(out_dir / "run_manifest.json", manifest)

    if args.config:
        cfg_path = Path(args.config)
        if cfg_path.exists():
            shutil.copy2(cfg_path, out_dir / "config_snapshot.yaml")

    train_result = trainer.train()
    trainer.save_model(str(out_dir / "final"))
    tokenizer.save_pretrained(str(out_dir / "final"))

    metrics = dict(train_result.metrics)
    if dev_dataset is not None:
        eval_metrics = trainer.evaluate()
        for key, value in eval_metrics.items():
            metrics[f"final_{key}"] = value

    save_json(out_dir / "metrics.json", metrics)
    metrics_out = Path(args.metrics_out) if args.metrics_out else out_dir / "metrics_summary.json"
    save_json(metrics_out, metrics)

    print(
        "[real-sft] "
        f"train={len(train_examples)} dev={len(dev_examples)} "
        f"output={out_dir} metrics={metrics_out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
