# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.0030 | 0.9970 | 0.7483 |
| DPO | 0.0030 | 0.9970 | 0.7564 |
| SimPO | 0.0030 | 0.9970 | 0.7564 |

结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。
