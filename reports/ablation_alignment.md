# 消融实验：SFT vs DPO vs SimPO

| 方法 | FactScore | InterceptionRate | Avg RiskScore |
|---|---:|---:|---:|
| SFT | 0.5042 | 0.9883 | 0.4604 |
| DPO | 0.5015 | 0.9883 | 0.4722 |
| SimPO | 0.5015 | 0.9883 | 0.4722 |

结论：在当前样例上，SimPO/DPO 相较 SFT 在安全侧更稳健（风险分更低）。
