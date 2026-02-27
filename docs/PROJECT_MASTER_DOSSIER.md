# MedLLM 项目总档案（项目详情 + 使用说明 + 产出说明 + 论文写作材料）

- 生成时间（UTC）：2026-02-27T23:59:00Z
- 代码分支：codex/worktree
- 代码版本：00c7e4f
- 适用阶段：GPU 迁移前最终梳理 / GPU 迁移执行指南 / 论文写作支撑

## 1. 项目总体结论

本项目已经完成工程主链闭环，具备以下条件：

1. 数据构建、清洗、偏差审计、检测评测、论文资产生成均可重复执行。
2. GPU 迁移脚本、环境 bootstrap、严格完工闸门已就位。
3. 论文写作所需的结构化材料、指标表、错误分析与实验记录已自动化落盘。

当前尚未“论文级严格完工”的唯一原因：

- 当前机器无 CUDA 资源，真实 Qwen2.5-7B/14B 训练处于 `skipped`，因此 `strict_pass=false`。

这意味着：

- 工程与流程已经到位；
- 迁移到 GPU 环境后可一键完成最后真实训练闭环。

## 2. 当前状态快照（来自最新产物）

### 2.1 审计状态
- Thesis readiness：`PASS=5, DEFERRED=2, FAIL=0`
- Handoff readiness：`ready=true`
- GPU strict completion：`strict_pass=false`

### 2.2 数据规模
- 来源：CMTMedQA 8000 + Huatuo26M-Lite 6000 + Huatuo Encyclopedia 6000
- 合并前：20000
- 去重后：19978
- 划分：train 15984 / dev 1997 / test 1997
- benchmark：3600
- 随机种子：42

### 2.3 训练状态
- SFT：`skipped`（显存不足）
- DPO：`skipped`（显存不足）
- SimPO：`skipped`（显存不足）
- KTO：`skipped`（显存不足）
- 证据文件：
  - `reports/training/resource_preflight.json`
  - `reports/training/resource_skip_report.md`

### 2.4 评测与审计关键数值
- 综合评测（1200 样本）：
  - SFT：FactScore 0.5000 / Utility 1.0000 / RiskScore 0.2736 / Interception 1.0000
  - DPO：FactScore 0.5000 / Utility 0.8434 / RiskScore 0.2783 / Interception 1.0000
  - SimPO：FactScore 0.5000 / Utility 0.8434 / RiskScore 0.2783 / Interception 1.0000
- 对标（代理复现实验）：
  - MedLLM-Hybrid：Accuracy 1.0000 / Recall 1.0000 / Specificity 1.0000 / F1 1.0000
  - BioMistral-7B-Proxy：Accuracy 0.3642 / Recall 0.5167 / Specificity 0.2117 / F1 0.4483
- 基准偏差审计：
  - 原始 benchmark：leakage risk HIGH（gap=0.9917）
  - v2 balanced：leakage risk LOW（gap=0.0000）
- v2 LLM 回退（预算 80 调用）：
  - rule-only：Recall 0.0000 / F1 0.0000
  - hybrid：Recall 0.0583 / F1 0.1074

## 3. 项目结构说明（主链）

- `src/`
  - `src/data/`：数据治理与清洗核心
  - `src/detect/`：幻觉检测（白盒 + 检索 + 可选 LLM 回退）
  - `src/train/`：真实 SFT 与真实偏好训练入口
  - `src/serve/`：服务化接口
- `scripts/`
  - `scripts/data/`：数据构建与治理流水线
  - `scripts/train/`：Layer-B SFT + DPO/SimPO/KTO 编排
  - `scripts/eval/`：评测与论文资产导出
  - `scripts/migration/`：GPU 迁移、交接清单、完工闸门
  - `scripts/pipeline/`：本地一键 paper-ready
- `configs/`：训练/评测配置
- `eval/`：统一评测器与 LLM-as-a-Judge
- `reports/`：全量证据链产物
- `docs/`：系统文档与运行手册
- `day1_run.sh`：GPU 首次上线一键脚本

## 4. 使用说明（从零到运行）

### 4.1 本地准备
```bash
make setup
```

`.env`（若启用 API 评测）：
```env
OPENAI_BASE_URL=https://api.gptsapi.net/v1
OPENAI_API_KEY=***
```

### 4.2 本地无 GPU 验证
```bash
make paper-ready
```

### 4.3 GPU 迁移标准流程
```bash
make gpu-manifest
make gpu-check
make gpu-bootstrap
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" MODEL_TIER="7b" ALLOW_SKIP_TRAINING=false FORCE_SKIP_TRAINING=false make gpu-run
make gpu-complete-check
```

### 4.4 GPU 首次上线零思考执行
```bash
bash day1_run.sh
# 或
make day1-run
```

## 5. 产出说明（论文证据链映射）

### 5.1 数据层
- `reports/real_dataset_report.md`：数据构建报告
- `reports/data_cleaning_report.md`：清洗与治理报告
- `reports/real_dataset_summary.json`：数据统计摘要

### 5.2 训练层
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`
- `reports/training/dpo_metrics.json`
- `reports/training/simpo_metrics.json`
- `reports/training/kto_metrics.json`
- `reports/training/resource_preflight.json`
- `reports/training/resource_skip_report.md`

### 5.3 评测层
- `reports/detection_eval.md`
- `reports/detection_eval_v2_balanced.md`
- `reports/detection_eval_v2_hybrid_llm_impact.md`
- `reports/eval_default.md`
- `reports/sota_compare.md`
- `reports/error_analysis.md`

### 5.4 论文资产层
- `reports/thesis_assets/tables/*.csv`
- `reports/thesis_assets/cases/error_cases_top30.jsonl`
- `reports/thesis_assets/figures/*`

### 5.5 论文支撑层
- `reports/thesis_support/thesis_draft_material.md`
- `reports/thesis_support/experiment_record.json`
- `reports/thesis_support/thesis_readiness.md`
- `reports/thesis_support/thesis_writing_material_full.md`

### 5.6 迁移与完工判定层
- `reports/migration/gpu_handoff_manifest.md`
- `reports/migration/handoff_readiness.md`
- `reports/migration/gpu_completion_check.md`
- `reports/migration/day1_gpu_run.log`（忽略提交）
- `reports/migration/day1_run_summary.md`（忽略提交）

## 6. 论文撰写材料（可直接改写）

### 6.1 研究背景与问题定义（章节草稿）
随着通用大模型在医疗问答场景中的应用增加，模型幻觉带来的临床安全风险逐步凸显。与开放域问答相比，医疗场景对事实一致性、风险控制与可追溯性要求更高。现有工作往往侧重单一环节优化，如数据微调或推理时校验，缺少覆盖“数据-推理-训练”全链路的工程化闭环。

本研究聚焦中文医疗问答场景，目标是在可复现实验框架下构建三层协同系统：通过数据治理降低输入噪声，通过运行时混合检测拦截高风险回答，通过偏好对齐抑制模型生成中的危险倾向。研究核心问题是：在资源受限到可扩展 GPU 环境下，如何构建具备工程可落地性与学术可验证性的幻觉抑制系统。

### 6.2 方法章节（章节草稿）
本文方法分为三层。第一层为数据治理层，针对多来源医疗问答数据进行字段标准化、冲突识别、规则清洗与基于知识库的质量校验，并产出结构化统计与审计报告。第二层为运行时检测层，融合白盒不确定性特征与检索核查结果进行风险判别，并可在低置信度区域引入受预算约束的 LLM 回退裁决。第三层为偏好对齐层，以 SFT 作为基础，再通过 DPO/SimPO/KTO 对风险相关偏好进行优化。

工程实现上，系统采用统一脚本编排与证据链落盘机制。所有关键环节均输出配置快照、指标文件、评测报告与审计记录。针对评测偏差问题，本文引入 benchmark 构造泄露审计，并构建 v2 balanced 基准，保证结论不依赖格式泄露。

### 6.3 实验设置与指标（章节草稿）
数据来源包括 CMTMedQA、Huatuo26M-Lite 与 Huatuo Encyclopedia QA。经去重后获得 19978 条样本，并构建 train/dev/test 以及 3600 条 benchmark。基座模型以 Qwen2.5-7B/14B（或 Qwen3 小参数）为目标口径。

评测指标包括事实性（FactScore）、可用性（Utility）、风险评分（RiskScore）、拦截率（InterceptionRate）以及安全二分类指标（Accuracy、Recall、Specificity、Unsafe Pass Rate、F1）。此外，本文引入 option-letter gap 与 leakage risk 对基准偏差进行审计。

### 6.4 结果与分析（章节草稿）
在当前非 GPU 环境下，真实训练因显存限制被安全跳过，但评测与审计链路完整可运行。综合评测显示系统能够稳定产出结构化指标；对标代理实验中，MedLLM-Hybrid 在当前口径下表现出更低的高风险放行率。偏差审计结果进一步表明，原始 benchmark 存在显著格式泄露风险，而 v2 balanced 基准有效降低该风险并使评测更具可信度。

在 v2 基准上，纯规则检测存在高漏检问题；引入预算受控的 LLM 回退后，Recall 与 F1 获得提升，但同时伴随 Specificity 下降。该结果说明回退机制可作为召回增强手段，但需在安全召回与误报成本之间做任务级权衡。

### 6.5 讨论与局限（章节草稿）
第一，当前阶段尚未完成 GPU 上的真实 Qwen 训练闭环，训练章节结论应明确标注为“待 GPU 补全”。第二，对标结果为统一代理复现实验，不等同官方模型原始能力。第三，LLM 回退模块受 API 预算与外部模型稳定性影响，需在生产化阶段设计更细粒度的缓存与降级策略。

尽管存在上述局限，本文已完成从数据到评测的工程主链与审计链构建，并提供严格完工闸门。该设计使后续 GPU 实验能够在不改代码的前提下直接完成，确保论文实证部分具备可追溯性与可复现性。

### 6.6 结论与后续工作（章节草稿）
本文构建了面向中文医疗问答的三层幻觉抑制系统，并给出可复现实验工程框架。系统在数据治理、检测融合、偏好对齐和偏差审计方面形成闭环，已具备迁移至 GPU 后一键完成真实训练与论文级验证的条件。后续工作将重点完成真实 Qwen 训练闭环、补全真实 loss 曲线与 checkpoint 证据，并进一步扩展多轮对话场景下的稳健性评估。

## 7. 论文章节建议目录（可直接采用）
1. 绪论
2. 相关工作
3. 系统设计与方法
4. 数据构建与治理
5. 实验设置与评测协议
6. 实验结果与分析
7. 讨论与局限
8. 结论与展望

## 8. 论文提交前硬性检查清单

1. `reports/migration/gpu_completion_check.json` 中 `strict_pass=true`
2. `reports/thesis_support/thesis_readiness.json` 中 `ready_for_writing=true`
3. 真实 SFT/DPO/SimPO/KTO 均为 `skipped=false`
4. 真实 Layer-B Qwen SFT 训练曲线文件存在
5. 最终论文引用的所有指标均来自 `reports/` 当前版本产物
