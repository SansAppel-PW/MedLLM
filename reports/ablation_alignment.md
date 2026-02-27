# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.0625 | 0.8750 | 0.6679 |
| DPO | 0.0625 | 0.8750 | 0.6747 |
| SimPO | 0.0625 | 0.8750 | 0.6747 |

结论：在当前样例上，SFT 的平均风险分最低，DPO/SimPO 未体现出额外安全收益。
