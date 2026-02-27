#!/usr/bin/env python3
"""Prepare a tiny local causal LM for deterministic real-alignment fallback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast


def build_tokenizer(out_dir: Path) -> PreTrainedTokenizerFast:
    # Keep vocab tiny but include common symbols for zh/en medical prompts.
    base_tokens = [
        "[PAD]",
        "[UNK]",
        "[BOS]",
        "[EOS]",
        "User",
        "Assistant",
        "医生",
        "患者",
        "建议",
        "禁忌",
        "剂量",
        "药物",
        "治疗",
        "症状",
        "风险",
        "高",
        "低",
        "。",
        "，",
        "：",
        "\n",
    ]
    vocab = {tok: idx for idx, tok in enumerate(base_tokens)}
    tokenizer = Tokenizer(WordLevel(vocab=vocab, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    fast = PreTrainedTokenizerFast(
        tokenizer_object=tokenizer,
        bos_token="[BOS]",
        eos_token="[EOS]",
        unk_token="[UNK]",
        pad_token="[PAD]",
    )
    fast.save_pretrained(out_dir)
    return fast


def ensure_model(out_dir: Path) -> None:
    config_path = out_dir / "config.json"
    model_path = out_dir / "model.safetensors"
    tokenizer_json = out_dir / "tokenizer.json"
    if config_path.exists() and model_path.exists() and tokenizer_json.exists():
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = build_tokenizer(out_dir)

    cfg = GPT2Config(
        vocab_size=len(tokenizer),
        n_positions=256,
        n_ctx=256,
        n_embd=128,
        n_layer=2,
        n_head=2,
        bos_token_id=tokenizer.bos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
    )
    model = GPT2LMHeadModel(cfg)
    model.save_pretrained(out_dir)

    meta = {
        "model_type": "offline_tiny_gpt2_fallback",
        "vocab_size": len(tokenizer),
        "n_layer": cfg.n_layer,
        "n_head": cfg.n_head,
        "n_embd": cfg.n_embd,
        "max_positions": cfg.n_positions,
    }
    (out_dir / "fallback_model_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare tiny local fallback model for real alignment")
    parser.add_argument("--output-dir", default="checkpoints/fallback_models/alignment_tiny_gpt2")
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    ensure_model(out_dir)
    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
