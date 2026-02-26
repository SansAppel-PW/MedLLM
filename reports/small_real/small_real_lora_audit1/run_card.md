# Small Real Run Card

- task: `small_real_pipeline`
- git_commit: `d4e75ebe112cca811486f052fc7b3663f38b9f95`
- model_name: `/Users/bibo/.cache/huggingface/hub/models--sshleifer--tiny-gpt2/snapshots/5f91d94bd9cd7190a9f3216ff93cd1dd95f2c7be`
- seed: `42`
- config: `configs/train/sft_real.yaml`
- train_samples/dev_samples: 1 / 1

## Train Metrics
- train_loss: 10.734733581542969
- final_eval_loss: 10.736883163452148

## Eval Metrics
- exact_match: 0.0
- rouge_l_f1: 0.0
- char_f1: 0.0

## Artifacts
- manifest: `checkpoints/small_real/small_real_lora_audit1/run_manifest.json`
- train_metrics: `reports/training/small_real_lora_audit1_metrics.json`
- eval_metrics: `reports/small_real/small_real_lora_audit1/eval_metrics.json`
- loss_curve: `reports/small_real/small_real_lora_audit1/loss_curve.png`
- predictions: `reports/small_real/small_real_lora_audit1/predictions.jsonl`
