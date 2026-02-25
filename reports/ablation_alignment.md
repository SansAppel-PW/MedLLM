# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.0017 | 0.9967 | 0.7477 |
| DPO | 0.0017 | 0.9967 | 0.7560 |
| SimPO | 0.0017 | 0.9967 | 0.7560 |

结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。
