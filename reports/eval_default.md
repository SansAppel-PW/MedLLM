# 综合评测报告

| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |
|---|---:|---:|---:|---:|
| SFT | 0.0250 | 1.0000 | 0.7346 | 1.0000 |
| DPO | 0.0333 | 0.8464 | 0.7233 | 0.9833 |
| SimPO | 0.0333 | 0.8464 | 0.7233 | 0.9833 |

## Win Rate (offline proxy quality = factscore + 1-risk)
- DPO vs SFT: 0.0750
- SimPO vs SFT: 0.0750

## Win Rate (LLM-as-a-Judge)
- DPO vs SFT: status=disabled win_rate=0.0000 detail=set --enable-llm-judge to enable
- SimPO vs SFT: status=disabled win_rate=0.0000 detail=set --enable-llm-judge to enable
- Judge config: `reports/judge/winrate/judge_config.json`
- Judge env vars: `THIRD_PARTY_API_KEY`, `THIRD_PARTY_BASE_URL`
