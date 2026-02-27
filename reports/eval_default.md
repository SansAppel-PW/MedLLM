# 综合评测报告

| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |
|---|---:|---:|---:|---:|
| SFT | 0.0625 | 1.0000 | 0.6679 | 0.8750 |
| DPO | 0.0625 | 0.8419 | 0.6747 | 0.8750 |
| SimPO | 0.0625 | 0.8419 | 0.6747 | 0.8750 |

## Win Rate (offline proxy quality = factscore + 1-risk)
- DPO vs SFT: 0.0437
- SimPO vs SFT: 0.0437

## Win Rate (LLM-as-a-Judge)
- DPO vs SFT: status=skipped win_rate=0.0000 detail=missing THIRD_PARTY_API_KEY
- SimPO vs SFT: status=skipped win_rate=0.0000 detail=missing THIRD_PARTY_API_KEY
- Judge config: `reports/judge/winrate/judge_config.json`
- Judge env vars: `THIRD_PARTY_API_KEY`, `THIRD_PARTY_BASE_URL`
