# DPO Beta 消融报告（Small-Real）

- 运行数: 3
- CSV: `reports/thesis_assets/tables/dpo_beta_ablation.csv`
- JSON: `reports/thesis_assets/tables/dpo_beta_ablation.json`

| run_tag | beta | pair_count | steps | train_loss | acc_before | acc_after | gain |
|---|---:|---:|---:|---:|---:|---:|---:|
| small_real_dpo_ablation_beta005 | 0.05 | 2 | 4 | 0.693198 | 0.0000 | 0.0000 | 0.0000 |
| small_real_dpo_ablation_beta010 | 0.1 | 2 | 4 | 0.693248 | 0.0000 | 0.0000 | 0.0000 |
| small_real_dpo_ablation_beta020 | 0.2 | 2 | 4 | 0.693349 | 0.0000 | 0.0000 | 0.0000 |

## 结论
- 最优 beta: `0.05`，pref_accuracy_after=0.0000。
- 注意：当前样本数较小（<20），仅作流程验证，不可作为论文主结论。
