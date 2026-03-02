# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.5165 | 0.2374 | 0.2189 |
| DPO | 0.4491 | 0.2374 | 0.2359 |
| SimPO | 0.4491 | 0.2374 | 0.2359 |

结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。
