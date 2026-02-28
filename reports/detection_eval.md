# 幻觉检测离线评测报告

## 指标
- Accuracy: 0.5250
- Precision: 0.5128
- Recall: 1.0000
- F1: 0.6780
- TP/FP/TN/FN: 100/95/5/0
- FPR: 0.9500
- FNR: 0.0000
- 样本数: 200

## 样例明细（前10条）
| id | expected | predicted | score |
|---|---|---|---|
| medqa_validation_000000_pos | low | high | 0.7809 |
| medqa_validation_000000_neg | high | high | 0.7743 |
| medqa_validation_000001_pos | low | high | 0.7743 |
| medqa_validation_000001_neg | high | high | 0.7743 |
| medqa_validation_000002_pos | low | high | 0.7466 |
| medqa_validation_000002_neg | high | high | 0.7123 |
| medqa_validation_000003_pos | low | high | 0.7666 |
| medqa_validation_000003_neg | high | high | 0.8006 |
| medqa_validation_000004_pos | low | high | 0.7323 |
| medqa_validation_000004_neg | high | high | 0.7323 |

## 误判统计
- 高/中风险漏检（FN）: 0
- 低风险误报（FP）: 95
