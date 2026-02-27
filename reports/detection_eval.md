# 幻觉检测离线评测报告

## 指标
- Accuracy: 1.0000
- Precision: 1.0000
- Recall: 1.0000
- F1: 1.0000
- TP/FP/TN/FN: 600/0/600/0
- FPR: 0.0000
- FNR: 0.0000
- 样本数: 1200
- LLM 回退开关: False
- LLM 回退调用次数: 0
- LLM 回退提升次数: 0

## 样例明细（前10条）
| id | expected | predicted | score |
|---|---|---|---|
| medqa_validation_000000_pos | low | low | 0.0976 |
| medqa_validation_000000_neg | high | medium | 0.4500 |
| medqa_validation_000001_pos | low | low | 0.1066 |
| medqa_validation_000001_neg | high | medium | 0.4500 |
| medqa_validation_000002_pos | low | low | 0.1143 |
| medqa_validation_000002_neg | high | medium | 0.4500 |
| medqa_validation_000003_pos | low | low | 0.1267 |
| medqa_validation_000003_neg | high | medium | 0.4500 |
| medqa_validation_000004_pos | low | low | 0.1209 |
| medqa_validation_000004_neg | high | medium | 0.4500 |

## 误判统计
- 高/中风险漏检（FN）: 0
- 低风险误报（FP）: 0
