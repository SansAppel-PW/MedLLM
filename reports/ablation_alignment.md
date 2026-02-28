# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.0250 | 1.0000 | 0.7346 |
| DPO | 0.0333 | 0.9833 | 0.7233 |
| SimPO | 0.0333 | 0.9833 | 0.7233 |

结论：在当前样例上，DPO 的平均风险分最低，较 SFT 体现出更好的安全侧表现。
