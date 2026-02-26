# Main Results Dual View

> 口径约束：real/proxy 分表展示，论文中不得直接横向比较数值绝对大小。

## Real Results
| section | setting | metric | value | sample_count | evidence | note |
|---|---|---|---:|---:|---|---|
| generation | BaseModel (tiny-gpt2) | exact_match | 0.0 | 1 | reports/small_real/base_model_eval_metrics.json | small-real baseline |
| generation | BaseModel (tiny-gpt2) | rouge_l_f1 | 0.0 | 1 | reports/small_real/base_model_eval_metrics.json | small-real baseline |
| generation | LoRA Small-Real (small_real_lora_v13) | exact_match | 0.0 | None | reports/small_real/small_real_lora_v13/eval_metrics.json | fallback small-real closure |
| generation | LoRA Small-Real (small_real_lora_v13) | rouge_l_f1 | 0.0 | None | reports/small_real/small_real_lora_v13/eval_metrics.json | fallback small-real closure |
| generation | LoRA Small-Real (small_real_lora_v13) | train_loss | 10.734590888023376 | None | reports/training/small_real_lora_v13_metrics.json | fallback small-real closure |
| alignment | DPO (real) | pref_accuracy_after | 0.3715277777777778 | 288 | reports/training/dpo_real_metrics.json | real preference alignment |

## Proxy Results
| section | setting | metric | value | sample_count | evidence | note |
|---|---|---|---:|---:|---|---|
| alignment | DPO (proxy) | aligned_score | 0.787646 | 15984 | reports/training/dpo_metrics.json | proxy indicator, not directly comparable to real preference accuracy |
| alignment | SimPO (proxy) | aligned_score | 0.816895 | 288 | reports/training/simpo_metrics.json | proxy indicator, not directly comparable to real preference accuracy |
| alignment | KTO (proxy) | aligned_score | 0.5875 | 288 | reports/training/kto_metrics.json | proxy indicator, not directly comparable to real preference accuracy |
