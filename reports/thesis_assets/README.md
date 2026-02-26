# Thesis Assets

本目录用于论文写作时直接引用。

## 结构
- `tables/experiment_overview.csv`: 数据规模与训练结果总览
- `tables/main_results_real.csv`: 主结果（real 口径）
- `tables/main_results_proxy.csv`: 主结果（proxy 口径）
- `tables/main_results_dual_view.md`: real/proxy 分层展示与写作约束
- `tables/baseline_real_mainline.csv`: baseline 对照中的 real 主线模型
- `tables/baseline_proxy_background.csv`: baseline 对照中的 proxy/背景模型
- `tables/baseline_audit_dual_view.md`: baseline 双层展示
- `tables/detection_confusion.csv`: 检测混淆矩阵
- `tables/sota_compare_metrics.csv`: 对标实验指标（由 `run_sota_compare.py` 生成）
- `cases/error_cases_top30.jsonl`: 错误案例样本（由 `generate_error_analysis.py` 生成）
- `figures/pipeline_mermaid.md`: 流程图源码
- `figures/result_figure_notes.md`: 图表建议
