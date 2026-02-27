# 对标模型评测（代理复现实验）

> 说明：本报告采用统一输入答案的“系统策略代理”比较，用于离线方法学对照；
> 不代表官方 HuatuoGPT/BioMistral 完整能力，仅用于同口径复现实验与论文方法部分说明。

- Benchmark: `data/benchmark/real_medqa_benchmark_v2_balanced.jsonl`
- Knowledge base: `data/kg/real_medqa_reference_kb.jsonl`
- 样本数: 1200

| 系统 | Accuracy | Recall | Specificity | Unsafe Pass Rate | Risky Block Rate | F1 |
|---|---:|---:|---:|---:|---:|---:|
| BioMistral-7B-Proxy (whitebox) | 0.4908 | 0.7700 | 0.2117 | 0.2300 | 0.2317 | 0.6020 |
| MedLLM-Hybrid (ours) | 0.6075 | 0.3650 | 0.8500 | 0.6350 | 0.2417 | 0.4818 |
| MedQA-RAG-Proxy (retrieval) | 0.4992 | 0.0050 | 0.9933 | 0.9950 | 0.0050 | 0.0099 |
| HuatuoGPT-7B-Proxy (raw) | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |

## 结论
- 安全优先口径：`BioMistral-7B-Proxy (whitebox)` 的高风险放行率最低（Unsafe Pass Rate = 0.2300）。
- 平衡口径（Accuracy + Specificity - UnsafePass）：`MedLLM-Hybrid (ours)` 最优（0.8225）。
- 可作为论文中“系统级安全策略对比”的可复现实验。
