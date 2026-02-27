# 真实数据集构建报告

## 数据源（重建）
| 名称 | 数据集 | split | 采样量 | 许可 |
|---|---|---|---:|---|
| cmtmedqa | Suprit/CMtMedQA | train | 8000 | MIT |
| huatuo26m_lite | FreedomIntelligence/Huatuo26M-Lite | train | 6000 | Apache-2.0 |
| huatuo_encyclopedia | FreedomIntelligence/huatuo_encyclopedia_qa | train | 6000 | Apache-2.0 |

## 合并与切分
- 合并后样本数（去重前）: 20000
- 合并后样本数（去重后）: 19978
- 训练集: 15984
- 验证集: 1997
- 测试集: 1997

## Benchmark
- real_medqa_benchmark 样本数: 3600

注：该报告由已有本地产物重建，用于迁移同步后恢复 summary 口径。
