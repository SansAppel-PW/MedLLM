# 幻觉检测离线评测报告

## 指标
- Accuracy: 0.5000
- Precision: 0.0000
- Recall: 0.0000
- F1: 0.0000
- TP/FP/TN/FN: 0/0/600/600
- FPR: 0.0000
- FNR: 1.0000
- 样本数: 1200

## 样例明细（前10条）
| id | expected | predicted | score |
|---|---|---|---|
| medqa_validation_000000_pos | low | low | 0.0976 |
| medqa_validation_000000_neg | high | low | 0.0723 |
| medqa_validation_000001_pos | low | low | 0.1066 |
| medqa_validation_000001_neg | high | low | 0.0976 |
| medqa_validation_000002_pos | low | low | 0.1143 |
| medqa_validation_000002_neg | high | low | 0.1096 |
| medqa_validation_000003_pos | low | low | 0.1267 |
| medqa_validation_000003_neg | high | low | 0.1066 |
| medqa_validation_000004_pos | low | low | 0.1209 |
| medqa_validation_000004_neg | high | low | 0.1209 |

## 误判统计
- 高/中风险漏检（FN）: 600
- 低风险误报（FP）: 0
