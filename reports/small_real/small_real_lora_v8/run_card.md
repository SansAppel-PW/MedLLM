# Small Real Run Card

- task: `small_real_pipeline`
- git_commit: `e2788a814c2cf6dbc53f92433ab6f7659d59f101`
- model_name: `/Users/bibo/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be`
- seed: `42`
- config: `configs/train/sft_real.yaml`
- train_samples/dev_samples: 1 / 1

## Train Metrics
- train_loss: 10.734590888023376
- final_eval_loss: 10.736875534057617

## Eval Metrics
- exact_match: 0.0
- rouge_l_f1: 0.0
- char_f1: 0.0

## Artifacts
- manifest: `checkpoints/small_real/small_real_lora_v8/run_manifest.json`
- train_metrics: `reports/training/small_real_lora_v8_metrics.json`
- eval_metrics: `reports/small_real/small_real_lora_v8/eval_metrics.json`
- loss_curve: `reports/small_real/small_real_lora_v8/loss_curve.png`
- predictions: `reports/small_real/small_real_lora_v8/predictions.jsonl`
