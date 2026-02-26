# 综合评测报告

| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |
|---|---:|---:|---:|---:|
| SFT | 0.5000 | 1.0000 | 0.4195 | 1.0000 |
| DPO | 0.5000 | 0.8367 | 0.4305 | 1.0000 |
| SimPO | 0.5000 | 0.8367 | 0.4305 | 1.0000 |

## Win Rate (quality = factscore + 1-risk)
- DPO vs SFT: 0.0375
- SimPO vs SFT: 0.0375

## LLM-as-a-Judge (API)
- Judge model: `gpt-4o-mini`
- Judge samples: 6
- DPO vs SFT: 0.5833
- SimPO vs SFT: 0.5833
