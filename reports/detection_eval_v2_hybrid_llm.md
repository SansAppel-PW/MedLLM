# 幻觉检测离线评测报告

## 指标
- Accuracy: 0.5150
- Precision: 0.6731
- Recall: 0.0583
- F1: 0.1074
- TP/FP/TN/FN: 35/17/583/565
- FPR: 0.0283
- FNR: 0.9417
- 样本数: 1200
- LLM 回退开关: True
- LLM 回退调用次数: 80
- LLM 回退提升次数: 52

## 样例明细（前10条）
| id | expected | predicted | score |
|---|---|---|---|
| medqa_validation_000000_pos | low | medium | 0.0976 |
| medqa_validation_000000_neg | high | medium | 0.0723 |
| medqa_validation_000001_pos | low | medium | 0.1066 |
| medqa_validation_000001_neg | high | low | 0.0976 |
| medqa_validation_000002_pos | low | low | 0.1143 |
| medqa_validation_000002_neg | high | low | 0.1096 |
| medqa_validation_000003_pos | low | medium | 0.1267 |
| medqa_validation_000003_neg | high | low | 0.1066 |
| medqa_validation_000004_pos | low | medium | 0.1209 |
| medqa_validation_000004_neg | high | medium | 0.1209 |

## 误判统计
- 高/中风险漏检（FN）: 565
- 低风险误报（FP）: 17
