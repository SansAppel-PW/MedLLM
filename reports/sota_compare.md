# 对标模型评测（代理复现实验）

> 说明：本报告采用统一输入答案的“系统策略代理”比较，用于离线方法学对照；
> 不代表官方 HuatuoGPT/BioMistral 完整能力，仅用于同口径复现实验与论文方法部分说明。

- Benchmark: `data/benchmark/real_medqa_benchmark.jsonl`
- Knowledge base: `data/kg/real_medqa_reference_kb_merged.jsonl`
- 样本数: 120

| 系统 | Accuracy | Recall | Specificity | Unsafe Pass Rate | Risky Block Rate | F1 |
|---|---:|---:|---:|---:|---:|---:|
| MedQA-RAG-Proxy (retrieval) | 0.5250 | 1.0000 | 0.0500 | 0.0000 | 1.0000 | 0.6780 |
| MedLLM-Hybrid (ours) | 0.5250 | 1.0000 | 0.0500 | 0.0000 | 1.0000 | 0.6780 |
| BioMistral-7B-Proxy (whitebox) | 0.4083 | 0.6000 | 0.2167 | 0.4000 | 0.1667 | 0.5035 |
| HuatuoGPT-7B-Proxy (raw) | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |

## 结论
- 在当前代理评测中，`MedQA-RAG-Proxy (retrieval)` 的高风险放行率最低（Unsafe Pass Rate = 0.0000）。
- 可作为论文中“系统级安全策略对比”的可复现实验。
