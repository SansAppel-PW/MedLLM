# 幻觉检测离线评测报告

## 指标
- Accuracy: 0.9933
- Precision: 0.9989
- Recall: 0.9878
- F1: 0.9933
- TP/FP/TN/FN: 1778/2/1798/22
- FPR: 0.0011
- FNR: 0.0122
- 样本数: 3600

## 样例明细（前10条）
| id | expected | predicted | score |
|---|---|---|---|
| medqa_train_000000_pos | low | low | 0.0904 |
| medqa_train_000000_neg | high | high | 0.7654 |
| medqa_train_000001_pos | low | low | 0.1511 |
| medqa_train_000001_neg | high | high | 0.8082 |
| medqa_train_000002_pos | low | low | 0.1082 |
| medqa_train_000002_neg | high | high | 0.7904 |
| medqa_train_000003_pos | low | low | 0.1725 |
| medqa_train_000003_neg | high | high | 0.8511 |
| medqa_train_000004_pos | low | low | 0.1584 |
| medqa_train_000004_neg | high | high | 0.8082 |

## 误判统计
- 高/中风险漏检（FN）: 22
- 低风险误报（FP）: 2
