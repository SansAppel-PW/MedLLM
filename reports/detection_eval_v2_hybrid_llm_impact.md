# v2 Hybrid LLM Fallback Impact

- predictions: `reports/detection_predictions_v2_hybrid_llm.jsonl`
- samples: 1200
- split filter: `validation,test` (applied=True)
- llm_used: 500
- llm_promotions: 309

| variant | accuracy | precision | recall | f1 | specificity | fpr | fnr | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rule_only | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0 | 0 | 600 | 600 |
| hybrid_with_llm | 0.6075 | 0.7087 | 0.3650 | 0.4818 | 0.8500 | 0.1500 | 0.6350 | 219 | 90 | 510 | 381 |
| delta(hybrid-rule) | 0.1075 | 0.7087 | 0.3650 | 0.4818 | -0.1500 | 0.1500 | -0.3650 | 219 | 90 | -90 | -219 |
