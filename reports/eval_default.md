# 综合评测报告

| 模型 | Avg FactScore | Avg Utility | Avg RiskScore | InterceptionRate |
|---|---:|---:|---:|---:|
| SFT | 0.0030 | 1.0000 | 0.7483 | 0.9970 |
| DPO | 0.0030 | 0.8464 | 0.7564 | 0.9970 |
| SimPO | 0.0030 | 0.8464 | 0.7564 | 0.9970 |

## Win Rate (offline proxy quality = factscore + 1-risk)
- DPO vs SFT: 0.0440
- SimPO vs SFT: 0.0440

## Win Rate (LLM-as-a-Judge)
- DPO vs SFT: status=disabled win_rate=0.0000 detail=set --enable-llm-judge to enable
- SimPO vs SFT: status=disabled win_rate=0.0000 detail=set --enable-llm-judge to enable
- Judge config: `reports/judge/winrate/judge_config.json`
- Judge env vars: `THIRD_PARTY_API_KEY`, `THIRD_PARTY_BASE_URL`
