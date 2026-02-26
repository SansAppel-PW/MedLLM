# Benchmark Artifact Audit

- Benchmark: `data/benchmark/real_medqa_benchmark_v2_balanced.jsonl`
- Splits: `validation,test`
- Samples: 1200

| Risk Label | Count | Prefix Rate | Option-Letter Rate |
|---|---:|---:|---:|
| low | 600 | 1.0000 | 1.0000 |
| medium | 0 | 0.0000 | 0.0000 |
| high | 600 | 1.0000 | 1.0000 |

- Option-letter rate gap (low vs high): 0.0000
- Artifact leakage risk: **LOW**

## Interpretation
- HIGH: answer format strongly correlates with label; detection metrics may be inflated.
- MEDIUM: moderate correlation; report as potential bias and add robustness ablation.
- LOW: no obvious answer-format shortcut at this level.
