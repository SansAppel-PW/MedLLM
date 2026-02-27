# 论文初稿支撑材料（自动生成）

- 生成时间（UTC）: N/A
- 代码版本: `d665697535930366a7e9580642b4dbd84daa17bd`

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
- SFT: real
- DPO: real
- SimPO: real
- KTO: real
- 资源探测: accelerator=cuda, cuda_total_mem_gb=31.73
- 跳过报告: `reports/training/resource_skip_report.md`

## 4. 综合评测主结果
| model | factscore | utility | risk_score | interception_rate |
|---|---:|---:|---:|---:|
| SFT | 0.4971 | 1.0000 | 0.1008 | 0.0050 |
| DPO | 0.4971 | 0.8615 | 0.1102 | 0.0050 |
| SimPO | 0.4971 | 0.8615 | 0.1102 | 0.0050 |

## 5. 对标实验主结果（节选）
| name | accuracy | recall | specificity | unsafe_pass_rate | f1 |
|---|---:|---:|---:|---:|---:|
| BioMistral-7B-Proxy (whitebox) | 0.49083333333333334 | 0.77 | 0.21166666666666667 | 0.23 | 0.6019543973941368 |
| MedLLM-Hybrid (ours) | 0.6075 | 0.365 | 0.85 | 0.635 | 0.4818481848184819 |
| MedQA-RAG-Proxy (retrieval) | 0.49916666666666665 | 0.005 | 0.9933333333333333 | 0.995 | 0.009884678747940693 |
| HuatuoGPT-7B-Proxy (raw) | 0.5 | 0.0 | 1.0 | 1.0 | 0.0 |

## 6. 错误分析要点
- 主预测文件样本数: 1200
- 误判总数: 601
- 漏检数: 597
- 误报数: 4
- medllm_hybrid: 601
- 选项错配未识别: 597
- 选项类样本检索噪声: 4

## 7. 评测偏差审计
- Artifact leakage risk: LOW
- Option-letter gap(low vs high): 0.0
- 审计文件: `reports/thesis_support/benchmark_artifact_report.json`
- v2 leakage risk: LOW
- v2 option-letter gap(low vs high): 0.0
- v2 检测 Accuracy/Recall/F1: 0.5000/0.0000/0.0000
- LLM Judge 检测 Accuracy/Recall/F1: 0.7333/0.8500/0.7612
- v2 Hybrid(规则+LLM回退) Accuracy/Recall/F1: 0.6075/0.3650/0.4818
- v2 Hybrid 回退调用/提升: 500/309
- v2 Hybrid 相对规则增益(Recall/F1): 0.3650/0.4818

## 8. 论文撰写建议（可直接展开为章节）
1. 数据治理章节：阐述 CMeKG 校验与冲突样本处理流程。
2. 检测章节：解释混合检测为何提升 recall 并分析 specificity 风险。
3. 对齐章节：说明真实训练与资源受限跳过策略的证据边界。
4. 讨论章节：结合 Top 错误案例给出可执行改进方向。
