# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.4375 | 0.5000 | 0.2784 |
| DPO | 0.5312 | 0.5000 | 0.2382 |
| SimPO | 0.5312 | 0.2500 | 0.2263 |

结论：在当前样例上，SimPO/DPO 相较 SFT 在安全侧更稳健（风险分更低）。
