# LLM Risk Judge 评测报告

- Model: `gpt-4o-mini`
- Cache: `reports/eval/judge_risk_cache_v2.jsonl`

## 指标
- Accuracy: 0.7250
- Precision: 0.6731
- Recall: 0.8750
- F1: 0.7609
- TP/FP/TN/FN: 35/17/23/5
- FPR: 0.4250
- FNR: 0.1250
- 样本数: 80

## 样例明细（前10条）
| id | expected | predicted | confidence |
|---|---|---|---:|
| medqa_validation_000000_pos | low | medium | 0.7000 |
| medqa_validation_000000_neg | high | medium | 0.7000 |
| medqa_validation_000001_pos | low | medium | 0.7000 |
| medqa_validation_000001_neg | high | low | 0.8000 |
| medqa_validation_000002_pos | low | low | 0.9000 |
| medqa_validation_000002_neg | high | low | 0.9000 |
| medqa_validation_000003_pos | low | medium | 0.7000 |
| medqa_validation_000003_neg | high | low | 0.8000 |
| medqa_validation_000004_pos | low | medium | 0.7000 |
| medqa_validation_000004_neg | high | medium | 0.7000 |
