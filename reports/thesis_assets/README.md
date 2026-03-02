# Thesis Assets

本目录用于论文写作时直接引用。

## 结构
- `tables/experiment_overview.csv`: 数据规模与训练结果总览
- `tables/detection_confusion.csv`: 检测混淆矩阵
- `tables/sota_compare_metrics.csv`: 对标实验指标（由 `run_sota_compare.py` 生成）
- `cases/error_cases_top30.jsonl`: 错误案例样本（由 `generate_error_analysis.py` 生成）
- `figures/pipeline_mermaid.md`: 流程图源码
- `figures/result_figure_notes.md`: 图表建议
- `figures/loss_curve_latest.png`: 最新 small-real 训练 loss 折线图
- `figures/alignment_metrics_bar.png`: DPO/SimPO/KTO 对齐指标柱状图
- `figures/train_loss_compare_bar.png`: 主线训练损失对比柱状图
- `figures/dpo_beta_curve.png`: DPO beta 消融折线图
- `figures/conclusion_status_bar.png`: 结论状态分布柱状图
- `figures/figure_manifest.json`: 图表生成清单
