# Benchmark Artifact Audit

- Benchmark: `data/benchmark/real_medqa_benchmark.jsonl`
- Splits: `validation,test`
- Samples: 1200

| Risk Label | Count | Prefix Rate | Option-Letter Rate |
|---|---:|---:|---:|
| low | 600 | 1.0000 | 1.0000 |
| medium | 0 | 0.0000 | 0.0000 |
| high | 600 | 1.0000 | 0.0083 |

- Option-letter rate gap (low vs high): 0.9917
- Artifact leakage risk: **HIGH**

## Interpretation
- HIGH: answer format strongly correlates with label; detection metrics may be inflated.
- MEDIUM: moderate correlation; report as potential bias and add robustness ablation.
- LOW: no obvious answer-format shortcut at this level.
