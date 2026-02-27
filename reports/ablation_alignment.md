# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.4971 | 0.0050 | 0.1008 |
| DPO | 0.4971 | 0.0050 | 0.1102 |
| SimPO | 0.4971 | 0.0050 | 0.1102 |

结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。
