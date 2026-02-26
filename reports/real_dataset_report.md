# 真实数据集构建报告

## 数据源
| 名称 | 数据集 | split | 总规模 | 采样起点 | 采样量 | 许可 |
|---|---|---|---:|---:|---:|---|
| cmtmedqa | Suprit/CMtMedQA | train | 68023 | 54836 | 120 | MIT |
| huatuo26m_lite | FreedomIntelligence/Huatuo26M-Lite | train | 177703 | 4826 | 120 | Apache-2.0 |
| huatuo_encyclopedia | FreedomIntelligence/huatuo_encyclopedia_qa | train | 362420 | 25975 | 120 | Apache-2.0 |

## 合并与切分
- 合并后样本数（去重前）: 360
- 合并后样本数（去重后）: 360
- 训练集: 288
- 验证集: 36
- 测试集: 36

## Benchmark
- real_medqa_benchmark 样本数: 200（含正例与对抗负例）

## 产物
- `data/raw/real_sources/*.jsonl`
- `data/clean/real_sft_train.jsonl`
- `data/clean/real_sft_dev.jsonl`
- `data/clean/real_sft_test.jsonl`
- `data/benchmark/real_medqa_benchmark.jsonl`
