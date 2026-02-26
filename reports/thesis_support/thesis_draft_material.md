# 论文初稿支撑材料（自动生成）

- 生成时间（UTC）: N/A
- 代码版本: `a05b8344bdd917db1c87c931fe11caea52676a30`

## 1. 研究目标与创新点映射
- 目标一：以 KG 数据治理降低训练数据事实噪声。
- 目标二：以白盒不确定性 + 黑盒检索核查构建混合幻觉检测。
- 目标三：以 DPO/SimPO/KTO 偏好对齐抑制高风险医疗幻觉。

## 2. 数据与实验设置记录
- merged_after_dedup: 19978
- train/dev/test: 15984 / 1997 / 1997
- benchmark_count: 3600
- seed: 42

## 3. 训练执行状态
- SFT: skipped (FORCE_SKIP_TRAINING=true)
- DPO: skipped (FORCE_SKIP_TRAINING=true)
- SimPO: skipped (FORCE_SKIP_TRAINING=true)
- KTO: skipped (FORCE_SKIP_TRAINING=true)
- 资源探测: accelerator=mps, cuda_total_mem_gb=0.0
- 跳过报告: `reports/training/resource_skip_report.md`

## 4. 综合评测主结果
| model | factscore | utility | risk_score | interception_rate |
|---|---:|---:|---:|---:|
| SFT | 0.0017 | 1.0000 | 0.7477 | 0.9967 |
| DPO | 0.0017 | 0.8434 | 0.7560 | 0.9967 |
| SimPO | 0.0017 | 0.8434 | 0.7560 | 0.9967 |

## 5. 对标实验主结果（节选）
| name | accuracy | recall | specificity | unsafe_pass_rate | f1 |
|---|---:|---:|---:|---:|---:|
| MedQA-RAG-Proxy (retrieval) | 0.5 | 0.9983333333333333 | 0.0016666666666666668 | 0.0016666666666666668 | 0.6662958843159066 |
| MedLLM-Hybrid (ours) | 0.5 | 0.9966666666666667 | 0.0033333333333333335 | 0.0033333333333333335 | 0.6659242761692651 |
| BioMistral-7B-Proxy (whitebox) | 0.3641666666666667 | 0.5166666666666667 | 0.21166666666666667 | 0.48333333333333334 | 0.4483007953723789 |
| HuatuoGPT-7B-Proxy (raw) | 0.5 | 0.0 | 1.0 | 1.0 | 0.0 |

## 6. 错误分析要点
- 主预测文件样本数: 1200
- 误判总数: 600
- 漏检数: 2
- 误报数: 598
- medllm_hybrid: 600
- 选项类样本检索噪声: 596
- 选项错配未识别: 2
- 不确定措辞触发风险: 1

## 7. 论文撰写建议（可直接展开为章节）
1. 数据治理章节：阐述 CMeKG 校验与冲突样本处理流程。
2. 检测章节：解释混合检测为何提升 recall 并分析 specificity 风险。
3. 对齐章节：说明真实训练与资源受限跳过策略的证据边界。
4. 讨论章节：结合 Top 错误案例给出可执行改进方向。
