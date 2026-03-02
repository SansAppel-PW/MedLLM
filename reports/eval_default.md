# 综合评测报告

| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |
|---|---:|---:|---:|---:|
| SFT | 0.5165 | 1.0000 | 0.2189 | 0.2374 |
| DPO | 0.4491 | 0.6460 | 0.2359 | 0.2374 |
| SimPO | 0.4491 | 0.6460 | 0.2359 | 0.2374 |

## Win Rate (offline proxy quality = factscore + 1-risk)
- DPO vs SFT: 0.0105
- SimPO vs SFT: 0.0105

## Win Rate (LLM-as-a-Judge)
- DPO vs SFT: status=disabled win_rate=0.0000 detail=set --enable-llm-judge to enable
- SimPO vs SFT: status=disabled win_rate=0.0000 detail=set --enable-llm-judge to enable
- Judge config: `reports/judge/winrate/judge_config.json`
- Judge env vars: `THIRD_PARTY_API_KEY`, `THIRD_PARTY_BASE_URL`
