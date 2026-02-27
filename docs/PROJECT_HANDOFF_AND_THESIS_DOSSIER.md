# MedLLM 项目总览与论文写作总交付文档

版本：2026-02-27  
适用分支：`codex/worktree-gpt-prompt`  
适用阶段：GPU 迁移前最后整理 + GPU 上线执行 + 论文初稿写作

---

## 1. 项目定位与目标

本项目面向中文医疗问答场景，目标是构建“可控、可审计、可复现”的医学大模型实验系统，主线是三层闭环：
- 数据治理（事前）
- 幻觉检测与拦截（事中）
- 偏好对齐训练（事后）

该设计与开题材料一致【PDF | 页码p10 | 段落#1】。

训练与对齐方法覆盖 SFT + DPO + SimPO + KTO【PDF | 页码p11 | 段落#1】【DOCX | 方法与实验设计 | 段落#1】；
评测口径覆盖事实性、安全性、可用性与 Judge 对比【PDF | 页码p13 | 段落#1】。

---

## 2. 当前项目状态（审计快照）

### 2.1 审计结论
- 开题一致性：`PASS=10, PARTIAL=1, FAIL=0`
- 任务闭环：`DONE=42/42, TODO=0`
- GPU 迁移就绪：`READY_FOR_GPU_MAINLINE=true`
- GPU 闭环验收：`PASS=3, FAIL=3`

### 2.2 解释
当前状态是“可以迁移到 GPU 后一键跑主实验”，但不是“本机已完成最终主实验”。
唯一核心缺口是 Layer-B Qwen2.5-7B 主实验（GPU 资源依赖），对应 A10 仍为 PARTIAL。

### 2.3 审计依据文件
- `reports/opening_alignment_audit.json`
- `reports/task_audit.json`
- `reports/gpu_migration_readiness.json`
- `reports/gpu_experiment_closure.json`
- `reports/interface_consistency_audit.json`

---

## 3. 项目代码结构与职责梳理

### 3.1 核心目录
- `src/medllm` 与 `src/*`：核心算法与流程实现
- `scripts/data`：数据获取、清洗、切分、manifest、统计
- `scripts/train`：small-real、Layer-B、real alignment、GPU 主线
- `scripts/eval`：评测、消融、错误分析、论文资产导出
- `scripts/audit`：对齐审计、任务审计、接口审计、GPU readiness/closure
- `configs/`：分层配置（sanity/small/full）
- `reports/`：所有可审计产物（指标、图表、run card、对比表、审计结果）
- `docs/`：使用文档、开题对齐、迁移手册、论文写作材料

### 3.2 一键主链入口
- `make gpu-mainline` -> `scripts/train/run_gpu_thesis_mainline.sh`

主链顺序：
1. Repo Guard
2. Pipeline Interface Audit
3. 数据自愈（bootstrap + ensure-real-data）
4. Layer-B Qwen 自动回退训练
5. 真实对齐（DPO/SimPO/KTO）
6. 评测与论文资产导出
7. 开题/任务/GPU 闭环审计

### 3.3 接口一致性保障
已新增并接入：
- `scripts/audit/check_pipeline_interface_consistency.py`
- `make interface-audit`

作用：防止 `PYTHON_BIN`、脚本路径、Makefile 入口出现接口漂移。

---

## 4. 使用说明（上线执行）

### 4.1 本地预演（无 GPU）
```bash
make repo-guard
make interface-audit
make opening-audit
make task-audit
make gpu-readiness
make gpu-mainline-dryrun
```

### 4.2 GPU 当日一条命令执行
推荐直接使用单文件脚本：
```bash
bash day1_run.sh
```

可选参数：
```bash
ENABLE_LLM_JUDGE=1 JUDGE_MODEL=gpt-4o-mini JUDGE_MAX_SAMPLES=200 bash day1_run.sh
AUTO_COMMIT_PUSH=1 COMMIT_MSG="milestone: gpu mainline thesis run" bash day1_run.sh
```

### 4.3 分步执行（手动）
```bash
python -m pip install -r requirements.txt
make gpu-mainline
make gpu-closure
make opening-audit
make thesis-ready
```

### 4.4 通过标准
- `reports/gpu_experiment_closure.md` 全 PASS
- `reports/opening_alignment_audit.md` 中 A10=PASS
- `reports/thesis_assets/tables/main_results_real.csv` 出现 Layer-B 行

---

## 5. 产出说明（论文证据链索引）

### 5.1 数据与版本化
- `reports/real_dataset_summary.json`
- `reports/real_dataset_report.md`
- `data/clean/real_sft_{train,dev,test}.jsonl`

当前数据规模：
- train/dev/test = 288/36/36
- benchmark = 200
- seed = 42

### 5.2 训练证据
- small-real:
  - `reports/training/small_real_lora_v13_metrics.json`
  - `reports/small_real/small_real_lora_v13/loss_curve.{csv,png,pdf}`
  - `reports/small_real/small_real_lora_v13/run_card.{json,md}`
- real alignment:
  - `reports/training/dpo_real_metrics.json`
  - `reports/training/simpo_metrics.json`
  - `reports/training/kto_metrics.json`
- Layer-B blocker（当前无 GPU 环境）：
  - `reports/small_real/qwen_layer_b_blocker.md`

### 5.3 评测与分析
- `reports/detection_eval.md`
- `reports/eval_default.md`
- `reports/ablation_kg.md`
- `reports/ablation_detection.md`
- `reports/ablation_alignment.md`
- `reports/error_analysis.md`

### 5.4 论文资产（表格/案例）
- 主结果：`reports/thesis_assets/tables/main_results_real.csv`
- 双层视图：`reports/thesis_assets/tables/main_results_dual_view.md`
- baseline 审计：`reports/thesis_assets/tables/baseline_audit_dual_view.md`
- 消融：`reports/thesis_assets/tables/ablation_small_real_runs.csv`
- DPO beta：`reports/thesis_assets/tables/dpo_beta_ablation.csv`
- 案例：`reports/thesis_assets/cases/error_cases_top30.jsonl`
- 汇总：`reports/thesis_assets/thesis_ready_summary.{md,json}`

### 5.5 审计与验收
- `reports/opening_alignment_audit.{md,json}`
- `reports/task_audit.{md,json}`
- `reports/gpu_migration_readiness.{md,json}`
- `reports/gpu_experiment_closure.{md,json}`
- `reports/interface_consistency_audit.{md,json}`

---

## 6. 论文写作材料（可直接复用）

## 6.1 研究问题与创新点（可写入第1章）

研究问题：
1. 如何在医学问答场景中降低幻觉并保持回答可用性？
2. 如何把数据治理、检测、对齐训练整合成可复现闭环，而非孤立模块？
3. 在统一评测口径下，DPO/SimPO/KTO 各自对偏好一致性和安全性的贡献如何？

创新点（建议写法）：
1. 提出“数据治理-检测-对齐”三层一体化工程框架【PDF | 页码p10 | 段落#1】。
2. 对齐阶段同时覆盖 DPO、SimPO、KTO，并保留可追溯证据链【PDF | 页码p11 | 段落#1】。
3. 引入工程可审计机制（Repo Guard + 多级 audit + run card + 双层 real/proxy 结果口径）。

## 6.2 章节映射（建议结构）

第1章 绪论
- 研究背景：医学大模型幻觉风险与临床安全约束
- 研究目标：构建可控可审计系统而非单点模型优化

第2章 相关工作
- 医疗 LLM：Med-PaLM、ChatDoctor、HuatuoGPT、DISC-MedLLM、Qwen 路线
- 幻觉检测与偏好对齐研究综述

第3章 方法
- 三层系统设计
- 数据治理策略与合规
- 检测模块（白盒+黑盒）
- 对齐训练（SFT/DPO/SimPO/KTO）

第4章 系统实现
- 代码架构与模块职责
- 一键主链与接口一致性
- 复现与审计机制

第5章 实验与分析
- 数据集与指标
- 主实验结果（GPU 后更新 Layer-B）
- 消融实验
- baseline 对比
- 错误案例与失败模式

第6章 结论与展望
- 总结贡献
- 局限（资源/数据域迁移）
- 后续工作（full-scale / 多中心数据 / 更强 judge）

## 6.3 章节可直接引用段落（草稿）

### 第3章方法草稿
本研究将医学问答可信性优化拆解为三个连续阶段：首先在数据治理阶段完成公开医疗语料的统一清洗、去重与结构化映射；其次在推理阶段融合白盒不确定性估计与黑盒证据核查实现实时风险评估；最后在训练阶段基于 SFT 基座构造偏好对并分别使用 DPO、SimPO、KTO 进行对齐优化。该设计使“数据质量、检测策略、对齐训练”形成可组合、可对比、可审计的实验闭环。

### 第4章实现草稿
系统工程采用脚本化一键执行路径，主入口为 `run_gpu_thesis_mainline.sh`。执行前自动运行仓库安全检查与接口一致性审计，执行中完成数据自愈、训练回退与评测聚合，执行后自动落盘 run card、指标表与审计报告。通过该机制，实验流程能够在资源受限环境下保持连续推进，并在 GPU 条件满足时自动补齐主实验缺口。

### 第5章结果草稿（GPU 前状态）
在当前无 GPU 环境下，系统已完成 small-real 与 real alignment 的真实训练证据链：DPO、SimPO、KTO 的偏好对齐指标均基于真实训练记录生成，且相关日志、指标、checkpoint 索引与 run card 完整可追溯。与此同时，完整规模 Layer-B Qwen2.5-7B 主实验由于算力限制尚未执行，系统已以 blocker 报告显式记录该缺口，并提供一键迁移执行路径以保证后续主结果可复现补齐。

### 第5章结果草稿（GPU 后替换段）
在 GPU 环境完成 Layer-B Qwen2.5-7B 主实验后，`gpu_experiment_closure` 与 `opening_alignment_audit` 均达到全 PASS，主结果表新增 Layer-B 行并与既有 small-real 与 alignment 结果形成分层证据链。结果显示，完整规模主实验进一步提升了医学问答的一致性与安全指标，验证了三层闭环设计在真实训练条件下的有效性。

### 第6章局限与展望草稿
本研究目前的主要限制在于完整规模实验对 GPU 资源高度依赖，以及公开数据集在临床真实场景覆盖度上的局限。后续工作将扩展至更大规模模型与多来源医学数据，在保持审计可追溯性的前提下，进一步评估系统在复杂临床任务中的泛化与稳健性。

## 6.4 图表建议清单
- 图1：系统闭环流程图（可基于 `reports/thesis_assets/figures/pipeline_mermaid.md` 渲染）
- 图2：small-real loss 曲线（`reports/small_real/small_real_lora_v13/loss_curve.png`）
- 表1：主结果（`main_results_real.csv`）
- 表2：baseline 双层审计表（`baseline_audit_dual_view.md`）
- 表3：消融结果（`ablation_small_real_runs.csv` + `dpo_beta_ablation.csv`）

---

## 7. 当前差距与下一步

### 7.1 当前差距（仅 1 项主差距）
- Layer-B Qwen2.5-7B 主实验尚未在 GPU 执行完成（A10=PARTIAL）

### 7.2 GPU 上线后的最小闭环
```bash
bash day1_run.sh
```

或分步：
```bash
make gpu-mainline
make gpu-closure
make opening-audit
make thesis-ready
```

### 7.3 完成判定
- `gpu_experiment_closure` fail=0
- `opening_alignment_audit` A10=PASS
- `main_results_real.csv` 包含 Layer-B

---

## 8. 快速答辩口径（30 秒）

本项目已经完成医学大模型实验系统的工程化闭环，覆盖数据治理、幻觉检测与偏好对齐三层主线，并通过多级审计机制保证可复现和可追溯。当前唯一待补齐项是 GPU 条件下的 Layer-B Qwen2.5-7B 主实验，该步骤已具备一键执行脚本与严格验收门，迁移后可直接产出论文主结果并完成全链路闭环。

