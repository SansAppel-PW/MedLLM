# 幻觉检测离线评测报告

## 指标
- Accuracy: 0.4992
- Precision: 0.4286
- Recall: 0.0050
- F1: 0.0099
- TP/FP/TN/FN: 3/4/596/597
- FPR: 0.0067
- FNR: 0.9950
- 样本数: 1200
- LLM 回退开关: False
- LLM 回退调用次数: 0
- LLM 回退提升次数: 0

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
- 高/中风险漏检（FN）: 597
- 低风险误报（FP）: 4
