# v2 Hybrid LLM Fallback Impact

- predictions: `reports/detection_predictions_v2_hybrid_llm.jsonl`
- samples: 1200
- split filter: `validation,test` (applied=True)
- llm_used: 80
- llm_promotions: 52

| variant | accuracy | precision | recall | f1 | specificity | fpr | fnr | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rule_only | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 600 | 600 |
| hybrid_with_llm | 0.5150 | 0.6731 | 0.0583 | 0.1074 | 0.9717 | 0.0283 | 0.9417 | 35 | 17 | 583 | 565 |
| delta(hybrid-rule) | 0.0150 | 0.6731 | 0.0583 | 0.1074 | -0.0283 | 0.0283 | -0.0583 | 35 | 17 | -17 | -35 |
