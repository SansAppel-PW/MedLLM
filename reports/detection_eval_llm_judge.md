# LLM Risk Judge 评测报告

- Model: `gpt-4o-mini`
- Cache: `reports/eval/judge_risk_cache.jsonl`

## 指标
- Accuracy: 0.7333
- Precision: 0.6892
- Recall: 0.8500
- F1: 0.7612
- TP/FP/TN/FN: 51/23/37/9
- FPR: 0.3833
- FNR: 0.1500
- 样本数: 120

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
| medqa_validation_000003_neg | high | medium | 0.7000 |
| medqa_validation_000004_pos | low | medium | 0.7000 |
| medqa_validation_000004_neg | high | medium | 0.7000 |
