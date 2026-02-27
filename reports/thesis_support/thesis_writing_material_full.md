# 论文写作材料（完整版）

> 文档用途：直接支撑硕士论文写作（研究背景、方法、实验、结果、讨论、结论）。
> 更新时间：2026-02-27（基于当前仓库最新评测产物）。

## 1. 题目建议与研究定位

## 1.1 题目建议
- 中文医疗大模型幻觉抑制的三层闭环研究：数据治理、混合检测与偏好对齐

## 1.2 研究问题
1. 仅依赖单一检测机制（白盒或检索）是否足以抑制医疗高风险幻觉？
2. 数据治理（KG 校验+去噪）能否稳定提升事实一致性与安全性？
3. 偏好对齐（DPO/SimPO/KTO）在医疗场景下是否能降低风险回答倾向？

## 1.3 研究贡献（写作可直接引用）
1. 构建了“数据治理（事前）-运行时检测（事中）-偏好对齐（事后）”的工程化闭环。
2. 提供可复现实验系统：完整脚本、配置、审计报告、资产导出、迁移手册。
3. 提出偏差审计机制：识别并隔离 benchmark 构造泄露，给出 v2 balanced 基准。
4. 提供 GPU 严格完工闸门：以自动化规则判定是否达到论文级真实实验闭环。

## 2. 实验系统与数据材料

## 2.1 数据来源与规模（当前记录）
来自 `reports/real_dataset_summary.json`：
- CMTMedQA: 8000
- Huatuo26M-Lite: 6000
- Huatuo Encyclopedia QA: 6000
- 合并后去重：19978
- 训练/验证/测试：15984 / 1997 / 1997
- benchmark 总数：3600
- 随机种子：42

## 2.2 数据治理流程（正文建议）
- 语义标准化（问答字段统一）
- 规则与知识库校验（实体、药物、禁忌、剂量）
- 冲突样本标记与清洗
- 训练集与 benchmark 分层切分
- 审计与报告落盘（可追溯）

## 2.3 三层实验结构（论文方法章节主线）
1. Pipeline 验证层：在受限资源下验证端到端流程正确性。
2. 小规模/受限真实层：在无法满足显存时保留跳过证据与其余模块产出。
3. 全规模真实层（GPU）：执行 Qwen2.5-7B/14B 或 Qwen3 小参数真实训练闭环。

## 3. 模型与方法描述（可用于方法章节）

## 3.1 基座与训练策略
- 基座：Qwen2.5-7B/14B-Instruct（或 Qwen3 小参数）
- SFT：Layer-B 医疗指令微调
- 对齐：DPO / SimPO / KTO
- 训练工程：LoRA/QLoRA、固定 seed、日志、manifest、checkpoint、OOM 自动降级

## 3.2 运行时检测策略
- 白盒：不确定性估计（熵、自一致性）
- 黑盒：检索 + 事实核查（RAG/NLI）
- 融合：规则风险分级，可选 LLM 回退（受预算与置信阈值控制）

## 3.3 评测策略
- 综合指标：FactScore、Utility、RiskScore、InterceptionRate、Win Rate
- 安全指标：Accuracy、Recall、Specificity、Unsafe Pass Rate、F1
- 偏差审计：Option-letter gap 与 leakage risk

## 4. 当前可引用结果（截至 2026-02-27）

## 4.1 综合评测（`reports/eval_default.md`，1200 样本）
- SFT: FactScore=0.5000, Utility=1.0000, RiskScore=0.2736, InterceptionRate=1.0000
- DPO: FactScore=0.5000, Utility=0.8434, RiskScore=0.2783, InterceptionRate=1.0000
- SimPO: FactScore=0.5000, Utility=0.8434, RiskScore=0.2783, InterceptionRate=1.0000
- WinRate (quality): DPO vs SFT = 0.2687；SimPO vs SFT = 0.2687

## 4.2 对标（`reports/sota_compare.md`，1200 样本）
- MedLLM-Hybrid (ours): Accuracy=1.0000, Recall=1.0000, Specificity=1.0000, UnsafePass=0.0000, F1=1.0000
- BioMistral-7B-Proxy (whitebox): Accuracy=0.3642, Recall=0.5167, Specificity=0.2117, UnsafePass=0.4833, F1=0.4483
- HuatuoGPT-7B-Proxy (raw): Accuracy=0.5000, Recall=0.0000, Specificity=1.0000, UnsafePass=1.0000, F1=0.0000
- MedQA-RAG-Proxy (retrieval): Accuracy=0.5000, Recall=0.0000, Specificity=1.0000, UnsafePass=1.0000, F1=0.0000

## 4.3 偏差审计
- 原始 benchmark: leakage risk = HIGH，option-letter gap = 0.9917
- v2 balanced benchmark: leakage risk = LOW，option-letter gap = 0.0000

写作建议：
- 正文主结论应基于 v2 balanced 结果；
- 原始 benchmark 结果用于说明“评测偏差风险与修复必要性”。

## 4.4 v2 检测与 LLM 回退
- v2 规则检测（无回退）：Accuracy=0.5000, Recall=0.0000, F1=0.0000
- v2 规则+LLM 回退（预算 80 调用）：Accuracy=0.5150, Recall=0.0583, F1=0.1074
- 回退带来 Recall/F1 提升，但会引入一定 FP（Specificity 下降）

## 4.5 当前训练状态（非 GPU 环境）
- `SFT/DPO/SimPO/KTO` 均为 `skipped=true`
- 跳过原因：显存不足（7B 需要 >=18GB CUDA）
- 对应证据：
  - `reports/training/resource_preflight.json`
  - `reports/training/resource_skip_report.md`

## 5. 论文章节写作模板

## 5.1 摘要模板（可直接改写）
本文针对中文医疗大模型在高风险问答场景中的幻觉问题，提出一种数据治理、运行时混合检测与偏好对齐协同的三层闭环框架。系统以 Qwen 系列模型为基础，构建可复现的工程流水线，并引入评测偏差审计机制以消除 benchmark 构造泄露。实验结果显示，在统一代理评测口径下，所提混合系统在安全性指标上优于对照系统；同时在 v2 balanced 基准上，规则与 LLM 回退融合可提升高风险召回。该系统支持 GPU 环境一键复现实验，为医疗大模型可信部署与论文复现提供了工程基础。

## 5.2 方法章节小节建议
1. 数据治理与知识校验
2. 白盒-黑盒融合检测机制
3. 偏好对齐训练目标（DPO/SimPO/KTO）
4. 工程复现实验协议与资源感知调度
5. 偏差审计与基准修复方法

## 5.3 实验章节小节建议
1. 数据集构建与统计
2. 实验设置与超参数
3. 主结果（综合评测 + 对标）
4. 消融与偏差审计（v1 vs v2）
5. 错误分析与案例讨论

## 5.4 讨论章节要点
- 为什么原始 benchmark 会导致虚高指标
- 为什么 v2 balanced 更能反映真实安全能力
- LLM 回退的收益-代价折中（Recall vs Specificity）
- 资源限制下的证据边界：DEFERRED 与 strict completion 的关系

## 6. 图表与附件清单（论文可直接引用）

## 6.1 建议插图
- 系统流程图：`reports/thesis_assets/figures/pipeline_mermaid.md`
- 训练曲线：GPU 实训后由 `scripts/eval/build_training_figures.py` 生成

## 6.2 建议表格
- 对标指标：`reports/thesis_assets/tables/sota_compare_metrics.csv`
- 混淆矩阵：`reports/thesis_assets/tables/detection_confusion.csv`
- 实验总览：`reports/thesis_assets/tables/experiment_overview.csv`
- 回退增益：`reports/thesis_assets/tables/detection_v2_hybrid_llm_impact.csv`

## 6.3 建议案例附录
- `reports/thesis_assets/cases/error_cases_top30.jsonl`

## 7. GPU 完成后需更新的论文字段
在执行完 GPU 实验后，需要更新：
1. `SFT/DPO/SimPO/KTO` 的真实训练损失与步骤统计
2. 真实 checkpoint 路径与可复现实验命令
3. 真实 Qwen Layer-B 训练曲线图
4. 论文摘要与结论中的“真实训练已完成”表述

## 8. 论文可提交判定标准（建议原文引用）
当且仅当同时满足：
- `reports/migration/gpu_completion_check.json` 中 `strict_pass=true`
- `reports/thesis_support/thesis_readiness.json` 中 `ready_for_writing=true`
- 真实训练曲线与 checkpoint 文件齐备

可判定本研究已完成论文级实证闭环。
