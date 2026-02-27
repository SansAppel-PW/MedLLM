# 实验总体设计（阶段2）

## 0. 文档目的
本文件将开题材料约束转化为可执行实验主计划，明确：
1. 三层实验结构隔离（模拟验证 / 小规模真实训练 / 完整规模实验）。
2. baseline 与模型选择（含 Med-PaLM、ChatDoctor、HuatuoGPT、DISC-MedLLM、Qwen 体系）。
3. 参数规模、计算成本、训练可行性与论文对比意义。
4. 可复现证据链规范。

关联证据：`docs/OPENING_PROPOSAL_EVIDENCE.md`

## 1. 阶段启动风险评估（执行前）
### 1.1 技术风险
- 风险（历史项，已缓解）：仓库早期训练实现以 simulation/proxy 为主，和真实训练目标冲突。
- 当前状态：已补齐真实 SFT 与真实偏好对齐入口（DPO/SimPO/KTO），并保留 proxy 作为 Sanity 层。
- 剩余风险：Layer-B Qwen2.5-7B 主实验依赖 GPU 资源，未在本机无 GPU 环境补齐。

### 1.2 计算资源风险
- 风险：PPT 含 32B/235B 口径，可能超出硕士周期常规资源。
- 缓解：主线固定在 7B/14B（Qwen2.5）+ Qwen3 小模型；32B/235B 仅做零样本对照或报告级引用。

### 1.3 论文逻辑风险
- 风险：若只做模型指标对比，会弱化“数据治理-检测-对齐”的系统创新主线。
- 缓解：每个实验都绑定“对应模块贡献”，强制输出章节映射与消融解释。

### 1.4 数据质量风险
- 风险：真实数据与版本登记尚未闭环，容易引入泄漏与不可复现问题。
- 缓解：建立数据 split guard、数据版本哈希、采样配置与许可证落盘制度。

### 1.5 时间成本风险
- 风险：若先追大模型全量微调，可能挤占论文写作与验证时间。
- 缓解：采用“先小后大”节奏：Qwen3-4B -> Qwen2.5-7B -> Qwen2.5-14B。

## 2. 三层实验结构（硬隔离）
### 2.1 Layer-A：模拟验证层
- 目标：验证流程连通性，不用于论文主结论。
- 目录建议：
  - `configs/train/sim/*`
  - `reports/sim/*`
- 规则：所有报告必须显式标注 `SIMULATION_ONLY`。

### 2.2 Layer-B：小规模真实训练层（论文主干起点）
- 目标：真实 forward/backward + loss + checkpoint + 评测闭环，低成本快速迭代。
- 模型优先级：`Qwen3-4B`、`Qwen2.5-7B`。
- 规则：必须保存训练配置、数据版本、模型版本、commit hash。

### 2.3 Layer-C：完整规模实验层（论文主结论）
- 目标：在资源可承受范围做完整对比与消融。
- 模型优先级：`Qwen2.5-14B`（必要时补充 Qwen3-8B 作为效率对照）。
- 规则：只允许复用已验证过的 Layer-B pipeline，不允许跳步。

## 3. Baseline 与模型选择分析
## 3.1 文献与系统基线（必须覆盖）
| 基线 | 一手来源 | 公开性 | 参数规模信息 | 对比意义 |
|---|---|---|---|---|
| Med-PaLM 2 | [Nature 2024](https://www.nature.com/articles/s41591-024-03423-7) | 受限（非开源权重） | 报告强调专家级医疗问答能力 | 作为“闭源上界参考”，用于讨论能力边界与评价口径 |
| ChatDoctor | [arXiv:2303.14070](https://arxiv.org/abs/2303.14070), [GitHub](https://github.com/Kent0n-Li/ChatDoctor) | 开源工程 | 论文强调基于 LLaMA 与约10万医患对话 | 作为早期医疗对话微调范式基线 |
| HuatuoGPT / HuatuoGPT-II | [HuatuoGPT](https://arxiv.org/abs/2305.15075), [HuatuoGPT-II](https://arxiv.org/abs/2311.09774), [Repo](https://github.com/FreedomIntelligence/HuatuoGPT-II) | 开源 | HuatuoGPT-II repo 给出 7B / 13B / 34B 系列 | 作为中文医疗垂直模型核心对照 |
| DISC-MedLLM | [arXiv:2308.14346](https://arxiv.org/abs/2308.14346), [Repo](https://github.com/FudanDISC/DISC-MedLLM) | 开源 | 官方仓库说明当前版本基于 Baichuan-13B，指令数据约47万 | 作为中文医疗指令微调与评测体系对照 |
| Qwen 医学相关路线 | [Qwen2.5 report](https://arxiv.org/abs/2412.15115), [Qwen2.5 blog](https://qwenlm.github.io/blog/qwen2.5/), [Qwen3 report](https://arxiv.org/abs/2505.09388), [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/) | 开源模型生态 | Qwen2.5 覆盖 0.5B-72B；Qwen3 覆盖 0.6B-235B | 作为本论文主实验模型族，兼顾可训练性与扩展性 |

## 3.2 主实验模型（按你给定优先级）
| 模型 | 来源 | 参数规模 | 选择理由 | 论文定位 |
|---|---|---:|---|---|
| Qwen2.5-7B-Instruct | [HF Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) | 7.61B | 训练成本可控、社区成熟、适合作为主线起点 | 主实验模型A |
| Qwen2.5-14B-Instruct | [HF Model Card](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct) | 14.7B | 在可承受资源下提供更强上限 | 主实验模型B（完整规模） |
| Qwen3 小模型（4B/8B） | [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/) | 4B / 8B | 更低训练成本，适合作为效率与鲁棒性补充对照 | 补充实验模型 |

## 4. 参数规模与计算成本分析（训练可行性）
### 4.1 估算前提
- 权重显存粗估：
  - BF16：`参数量(B) * 2 GB`
  - 4-bit：`参数量(B) * 0.5 GB`
- 说明：真实训练还包含激活、梯度、优化器状态，实际显存显著高于权重占用。

### 4.2 成本/可行性表
| 模型 | 参数 | BF16权重约 | 4-bit权重约 | 推荐训练方式 | 可行性结论 |
|---|---:|---:|---:|---|---|
| Qwen3-4B | 4.0B | 8.0GB | 2.0GB | LoRA / QLoRA | 单卡 A100 可稳定跑小规模真实训练 |
| Qwen2.5-7B | 7.61B | 15.2GB | 3.8GB | LoRA / QLoRA（主推） | 论文主线最优起点，成本与效果平衡 |
| Qwen3-8B | 8.0B | 16.0GB | 4.0GB | LoRA / QLoRA | 可作为 7B 的平行效率对照 |
| Qwen2.5-14B | 14.7B | 29.4GB | 7.3GB | QLoRA（主推） | 完整规模实验可行，但训练时长与调参成本显著上升 |
| HuatuoGPT-II-13B | 13B | 26.0GB | 6.5GB | 推理对照优先 | 可做基线评测；从零重训成本偏高 |
| DISC-MedLLM(13B) | 13B | 26.0GB | 6.5GB | 推理对照优先 | 用作口径对比，避免额外大规模重训 |

### 4.3 论文合理性与对比价值
- 7B/14B/Qwen3 小模型路线能在硕士周期内给出“真实训练 + 完整消融 + 可复现”证据链。
- Med-PaLM/ChatDoctor/HuatuoGPT/DISC-MedLLM 的作用是“方法与能力参照系”，不要求全部重训。
- 对比价值来自三点：
  1. 同类中文医疗模型的安全性/事实性横向比较。
  2. 同一模型族内参数规模与训练策略的纵向比较。
  3. 是否由“数据治理 + 混合检测 + 对抗偏好对齐”带来可解释增益。

## 5. 评测设计与章节映射
### 5.1 指标组
- 事实性：FactScore、原子事实冲突率。
- 安全性：幻觉拦截率、危险建议放行率。
- 可用性：Rouge-L、任务完成率、响应可读性。
- 对齐有效性：SFT vs DPO vs SimPO vs KTO。

### 5.2 消融组
1. 去除 KG 清洗 vs 保留 KG 清洗。
2. 白盒检测 vs 黑盒检测 vs 混合检测。
3. 随机负样本 vs 对抗性负样本。

### 5.3 论文章节挂钩
- 第3章：数据治理与去泄漏。
- 第4章：幻觉检测系统。
- 第5章：偏好对齐与真实训练。
- 第6章：综合评测与消融。

## 6. 可复现机制（必须落盘）
每次真实实验都要保存：
1. `config.yaml` 快照与 override 记录。
2. 模型版本（base model id + revision）。
3. 数据版本（输入文件 hash + split 描述）。
4. 训练日志（loss、lr、step-time、eval）。
5. checkpoint 索引与最佳模型标记。
6. 代码版本（git commit hash）。

## 7. 本模块论文影响评估
1. 所属章节：`第3章实验设计`。
2. 是否形成完整实验小节：是（“实验总体设计与可行性分析”）。
3. 是否增强创新性：中等增强（把创新点映射到可执行实验矩阵）。
4. 是否增强严谨性：显著增强（建立参数-算力-证据链的可验证约束）。

结论：保留并作为后续实现的强约束文档。
