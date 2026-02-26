# Small Real Run Card

- task: `small_real_sft_offline`
- git_commit: `4e07a0cdc469cfcf21c01261405ffdaa02c52495`
- model_name: `/Users/bibo/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be`
- seed: `42`
- config: `configs/train/sft_real.yaml`
- train_samples/dev_samples: 1 / 1

## Train Metrics
- train_loss: 10.734709858894348
- final_eval_loss: 10.736878395080566

## Eval Metrics
- exact_match: 0.0
- rouge_l_f1: 0.0
- char_f1: 0.0

## Artifacts
- manifest: `checkpoints/small_real/tiny_gpt2_lora_v2/run_manifest.json`
- train_metrics: `reports/training/small_real_tiny_gpt2_lora_v2_metrics.json`
- eval_metrics: `reports/small_real/eval_metrics.json`
- loss_curve: `reports/small_real/loss_curve.png`
- predictions: `reports/small_real/predictions.jsonl`
