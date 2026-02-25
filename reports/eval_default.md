# 综合评测报告

| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |
|---|---:|---:|---:|---:|
| SFT | 0.4375 | 1.0000 | 0.2784 | 0.5000 |
| DPO | 0.5312 | 0.4375 | 0.2382 | 0.5000 |
| SimPO | 0.5312 | 0.3646 | 0.2263 | 0.2500 |

## Win Rate (quality = factscore + 1-risk)
- DPO vs SFT: 0.2500
- SimPO vs SFT: 0.3750
