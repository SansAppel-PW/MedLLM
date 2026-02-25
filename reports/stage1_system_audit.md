# Stage 1 系统结构审计报告（论文级重建）

## 0. 审计元信息
- 日期：2026-02-25
- 分支：`codex/worktree`
- 基线提交：`f06cfc85a657931d61f98435815c6c75ba3fe9c2`
- 开题材料证据：`docs/OPENING_PROPOSAL_EVIDENCE.md`

## 1. 阶段启动风险评估（执行前）
### 1.1 技术风险
- 风险：训练代码仍为模拟实现，无法提供真实 forward/backward、真实 loss、真实 checkpoint。
- 缓解：拆分三层实验路径（模拟验证/小规模真实训练/完整规模训练），先以 Qwen2.5-7B LoRA 打通真实闭环，再扩展 14B。

### 1.2 计算资源风险
- 风险：开题材料存在 32B/235B 口径，但当前仓库与依赖未体现可直接运行资源方案。
- 缓解：将 32B/235B 定位为“扩展实验”，主线固定 7B/14B；按 GPU 显存预算建立 batch、grad accumulation 与量化策略模板。

### 1.3 论文逻辑风险
- 风险：开题文本包含 Demo 表述，易与“论文级真实实验”主线冲突。
- 缓解：文档结构改为“系统证据链优先，Demo 仅展示层”，所有章节绑定真实实验记录与可复现证据。

### 1.4 数据质量风险
- 风险：当前工作区不存在 real_sft / real_benchmark / real_kb 文件，数据链未闭合。
- 缓解：先实现数据构建与版本登记闭环（hash、split、license、生成脚本参数）再进入真实训练。

### 1.5 时间成本风险
- 风险：若先追求大模型规模，会阻塞论文核心实验闭环。
- 缓解：阶段化推进，优先完成“可运行、可复现、可引用”的最小论文主链，再按算力上探。

## 2. 仓库现状扫描（事实）
### 2.1 结构与规模
- 文件总数：117
- `src/` 文件：34
- `scripts/` 文件：18
- `configs/` 文件：14
- `docs/` 文件：7
- `reports/` 文件：33

### 2.2 任务状态与交付完整性
- `scripts/audit/check_task_completion.py` 结果：42/42 标记 DONE。
- 但存在 1 项“DONE 且交付缺失”：`T105` 缺少 `data/kg/triples/*.jsonl`。

### 2.3 真实实验就绪性
- 当前训练数据规模仅：
  - `data/clean/sft_train.jsonl`: 1 行
  - `data/clean/sft_dev.jsonl`: 1 行
  - `data/clean/pref_seed_pairs.jsonl`: 2 行
- `real_*` 训练/评测关键文件缺失：
  - `data/clean/real_sft_train.jsonl`（缺失）
  - `data/clean/real_sft_dev.jsonl`（缺失）
  - `data/clean/real_pref_seed_pairs.jsonl`（缺失）
  - `data/benchmark/real_medqa_benchmark.jsonl`（缺失）
  - `data/kg/real_medqa_reference_kb.jsonl`（缺失）

### 2.4 训练实现真实性
- `src/train/sft_train.py`、`dpo_train.py`、`simpo_train.py`、`kto_train.py` 均明确为 simulation/mock/proxy 语义实现，不是参数训练。
- `README.md` 与 `docs/ACADEMIC_INTEGRITY.md` 同样显式声明当前是代理流程。

### 2.5 环境依赖就绪性
- 当前 Python 环境缺少关键训练依赖：`torch`、`transformers`、`datasets`、`trl`、`peft`、`pytest`。

## 3. 与开题材料目标的差距分析
### 3.1 已对齐点
- 架构方向一致：数据治理 + 混合检测 + 偏好对齐。[PDF: PG010L001][DOCX: T03R001][PPT: S011H002]
- 指标口径方向一致：FactScore/WinRate/Rouge-L/拦截率。[PDF: PG013L001][PPT: S015H006]
- 有基础模块框架与脚本骨架，便于迭代。

### 3.2 未对齐关键点
- “真实训练闭环”尚未建立（最关键断点）。
- “真实数据版本闭环”尚未建立（real_* 文件缺失）。
- “baseline 真实口径对比”尚未建立（当前为 proxy compare）。
- “可复现证据链”缺少 commit hash/data hash/config 快照落盘机制。

## 4. 重建 Roadmap（V1，按论文优先级）
1. 阶段1（当前）：系统结构审计与证据基线固化（本报告 + 开题证据提取）。
2. 阶段2：实验总体设计落盘（含三层实验隔离、baseline/模型规模/算力预算、可复现规范）。
3. 阶段3：框架搭建（逐模块）
   - 3.1 真实数据构建与版本登记模块
   - 3.2 真实 SFT（LoRA/QLoRA）训练模块
   - 3.3 真实 DPO/SimPO/KTO 对齐训练模块
4. 阶段4：真实训练闭环执行（小规模真实训练，含日志、loss、checkpoint、配置快照）。
5. 阶段5：评测体系闭环（事实性/安全性/可用性指标与消融）。
6. 阶段6：可视化系统（论文图表自动生成、误差案例可追溯）。
7. 阶段7：论文支撑文档系统（章节映射、实验证据索引、可复现附录）。

## 5. 本逻辑单元的论文影响评估
1. 属于论文章节：`第1章研究设计与技术路线`、`第3章实验设计总览`前置材料。
2. 是否形成完整实验小节：否（这是审计小节，不是实验结果小节）。
3. 是否增强创新性：间接增强（通过约束收敛与实验主线统一，避免创新点漂移）。
4. 是否增强严谨性：是（补齐“目标-代码-证据”一致性检查，降低论文口径风险）。

结论：保留该模块，作为后续真实实验章节的前置证据节点。

## 6. 下一逻辑单元入口
- 目标：落盘“实验总体设计文档（阶段2）”，明确三层实验隔离、baseline 对比矩阵、Qwen 7B/14B/Qwen3 小模型主线与算力可行性。
- 输出：`docs/EXPERIMENT_MASTER_PLAN.md`（下一提交）。
