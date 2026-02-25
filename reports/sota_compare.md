# 对标模型评测（代理复现实验）

> 说明：本报告采用统一输入答案的“系统策略代理”比较，用于离线方法学对照；
> 不代表官方 HuatuoGPT/BioMistral 完整能力，仅用于同口径复现实验与论文方法部分说明。

- Benchmark: `data/benchmark/real_medqa_benchmark.jsonl`
- Knowledge base: `data/kg/real_medqa_reference_kb.jsonl`
- 样本数: 1200

| 系统 | Accuracy | Recall | Specificity | Unsafe Pass Rate | Risky Block Rate | F1 |
|---|---:|---:|---:|---:|---:|---:|
| MedQA-RAG-Proxy (retrieval) | 0.5000 | 0.9983 | 0.0017 | 0.0017 | 0.9967 | 0.6663 |
| MedLLM-Hybrid (ours) | 0.5000 | 0.9967 | 0.0033 | 0.0033 | 0.9917 | 0.6659 |
| BioMistral-7B-Proxy (whitebox) | 0.3642 | 0.5167 | 0.2117 | 0.4833 | 0.1950 | 0.4483 |
| HuatuoGPT-7B-Proxy (raw) | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |

## 结论
- 在当前代理评测中，`MedQA-RAG-Proxy (retrieval)` 的高风险放行率最低（Unsafe Pass Rate = 0.0017）。
- 可作为论文中“系统级安全策略对比”的可复现实验。
