# 幻觉检测离线评测报告

## 指标
- Accuracy: 0.5000
- Precision: 0.5000
- Recall: 0.9967
- F1: 0.6659
- TP/FP/TN/FN: 598/598/2/2
- FPR: 0.9967
- FNR: 0.0033
- 样本数: 1200

## 样例明细（前10条）
| id | expected | predicted | score |
|---|---|---|---|
| medqa_validation_000000_pos | low | high | 0.7576 |
| medqa_validation_000000_neg | high | high | 0.7123 |
| medqa_validation_000001_pos | low | high | 0.7666 |
| medqa_validation_000001_neg | high | high | 0.7466 |
| medqa_validation_000002_pos | low | high | 0.7743 |
| medqa_validation_000002_neg | high | high | 0.7612 |
| medqa_validation_000003_pos | low | high | 0.7867 |
| medqa_validation_000003_neg | high | high | 0.7576 |
| medqa_validation_000004_pos | low | high | 0.7809 |
| medqa_validation_000004_neg | high | high | 0.7743 |

## 误判统计
- 高/中风险漏检（FN）: 2
- 低风险误报（FP）: 598
