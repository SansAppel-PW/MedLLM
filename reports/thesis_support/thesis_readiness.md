# Thesis Readiness Check

- PASS: 5
- DEFERRED: 2
- FAIL: 0

| ID | Requirement | Status | Note |
|---|---|---|---|
| R1 | 数据收集、清洗与防泄露系统代码及数据统计报告 | PASS | scripts/data/build_real_dataset.py | scripts/data/run_data_governance_pipeline.py | reports/real_dataset_report.md | reports/data_cleaning_report.md |
| R2 | 真实可复现微调系统（LoRA/QLoRA）及最优 checkpoint | DEFERRED | 训练包含 skipped/simulation，已记录跳过证据（reports/training/resource_skip_report.md）；状态=SFT:skipped, DPO:skipped, SimPO:skipped, KTO:skipped |
| R3 | 包含 API 自动评测的多维度指标对比表格 | PASS | eval/llm_judge.py | reports/eval_default.md | reports/sota_compare.md | reports/thesis_assets/tables/sota_compare_metrics.csv |
| R4 | 真实训练 Loss 下降曲线图（png/pdf） | DEFERRED | 真实 SFT 训练受限，当前仅具备跳过证据 |
| R5 | 系统说明文档（Readme、架构图、环境配置） | PASS | README.md | docs/ARCH.md | docs/DEPLOY.md | docs/RESOURCE_AWARE_EXECUTION.md |
| R6 | 论文初稿支撑材料（实验记录、结论说明、创新点论述） | PASS | reports/thesis_support/thesis_draft_material.md | reports/thesis_support/experiment_record.json | reports/error_analysis.md |
| R7 | 评测偏差审计（避免格式泄露导致指标虚高） | PASS | v2 偏差风险可接受（gap=0.0），原始基准偏差已被隔离 |
