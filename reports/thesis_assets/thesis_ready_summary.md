# Thesis Ready Summary

- Generated(UTC): 2026-02-28T01:18:09.285107+00:00
- Latest Small-Real Run: small_real_lora_v13

## Main Result Table
- CSV: `reports/thesis_assets/tables/main_results_small_real.csv`
- Real CSV: `reports/thesis_assets/tables/main_results_real.csv`
- Proxy CSV: `reports/thesis_assets/tables/main_results_proxy.csv`
- Dual View(MD): `reports/thesis_assets/tables/main_results_dual_view.md`

## Ablation/Control Table
- CSV: `reports/thesis_assets/tables/ablation_small_real_runs.csv`

## Alignment (Real DPO) Table
- CSV: `reports/thesis_assets/tables/alignment_real_dpo_runs.csv`

## DPO Beta Ablation
- CSV: `reports/thesis_assets/tables/dpo_beta_ablation.csv`

## Supporting Evidence
- Baseline Audit: `reports/thesis_assets/tables/baseline_audit_table.csv`
- Baseline Real Mainline: `reports/thesis_assets/tables/baseline_real_mainline.csv`
- Baseline Proxy Background: `reports/thesis_assets/tables/baseline_proxy_background.csv`
- Baseline Dual View: `reports/thesis_assets/tables/baseline_audit_dual_view.md`
- Qwen Layer-B Blocker: `reports/small_real/qwen_layer_b_blocker.md`
- Error Cases: `reports/thesis_assets/cases/error_cases_top30.jsonl`

## Thesis Writing Notes
- 主结果口径: 主结果采用 real/proxy 双层分表；small-real 仅作为工程闭环证据，不作为最终主结论。
- 消融口径: Across small_real_lora_v* runs to verify reproducibility and run stability.
- 对齐口径: real/proxy 按 simulation 标记自动分层呈现，禁止跨口径直接比较绝对数值。
- 局限性: Qwen2.5-7B Layer-B full experiment blocked by missing GPU/CUDA resources in current environment.
- 下一步: Run scripts/train/run_layer_b_qwen_autofallback.sh on >=24GB GPU and regenerate package.
