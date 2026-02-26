# Thesis Ready Summary

- Generated(UTC): 2026-02-26T04:38:59.489265+00:00
- Latest Small-Real Run: small_real_lora_v13

## Main Result Table
- CSV: `reports/thesis_assets/tables/main_results_small_real.csv`

## Ablation/Control Table
- CSV: `reports/thesis_assets/tables/ablation_small_real_runs.csv`

## Alignment (Real DPO) Table
- CSV: `reports/thesis_assets/tables/alignment_real_dpo_runs.csv`

## DPO Beta Ablation
- CSV: `reports/thesis_assets/tables/dpo_beta_ablation.csv`

## Supporting Evidence
- Baseline Audit: `reports/thesis_assets/tables/baseline_audit_table.csv`
- Qwen Layer-B Blocker: `reports/small_real/qwen_layer_b_blocker.md`
- Error Cases: `reports/thesis_assets/cases/error_cases_top30.jsonl`

## Thesis Writing Notes
- 主结果口径: Small-Real LoRA fallback evidence (engineering closure), not final thesis mainline.
- 消融口径: Across small_real_lora_v* runs to verify reproducibility and run stability.
- 对齐口径: Small-Real DPO real-training runs (if available) as alignment evidence.
- 局限性: Qwen2.5-7B Layer-B full experiment blocked by missing GPU/CUDA resources in current environment.
- 下一步: Run scripts/train/run_layer_b_qwen_autofallback.sh on >=24GB GPU and regenerate package.
