# GPU Experiment Closure Verification

- PASS: 3
- FAIL: 3

| ID | Requirement | Status | Detail | Evidence |
|---|---|---|---|---|
| G01 | Layer-B Qwen2.5-7B real SFT metrics | FAIL | Missing Layer-B metrics or invalid train_loss. | reports/training/layer_b_qwen25_7b_sft_metrics.json |
| G02 | Real DPO alignment evidence | PASS | DPO metrics are real and pair_count>0. | reports/training/dpo_real_metrics.json |
| G03 | Real SimPO alignment evidence | PASS | SimPO metrics are real and sample_count>0. | reports/training/simpo_metrics.json |
| G04 | Real KTO alignment evidence | PASS | KTO metrics are real and sample_count>0. | reports/training/kto_metrics.json |
| G05 | Opening alignment A10 should be PASS | FAIL | A10 status=PARTIAL. | reports/opening_alignment_audit.json |
| G06 | Main real result table should include Layer-B row | FAIL | Layer-B row not found in main_results_real.csv. | reports/thesis_assets/tables/main_results_real.csv |
