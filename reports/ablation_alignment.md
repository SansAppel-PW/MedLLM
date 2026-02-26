# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.5000 | 1.0000 | 0.2736 |
| DPO | 0.5000 | 1.0000 | 0.2783 |
| SimPO | 0.5000 | 1.0000 | 0.2783 |

结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。
