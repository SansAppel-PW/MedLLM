# Step 4 渐进式开发 Roadmap（论文导向）

## 0. 设计原则
- 分层执行：Sanity（流程验证）-> Small Real（小规模真实）-> Full（完整规模）。
- 每步必须有可验收产物与证据链，不满足即不进入下一步。
- 每次里程碑都绑定论文章节映射，避免无关开发。

## 1. 里程碑拆分

### M0 安全底座（必须先完成）
- 目标：防止数据/权重/密钥误入库。
- 产物：
  - `scripts/repo_guard.py`
  - `.gitignore` 强化规则
  - `.env.example`
- 验收标准：
  - `python scripts/repo_guard.py --mode preadd` 通过。
  - 人工构造违规样本时 Guard 能失败并给出明确原因。
- 论文映射：实验可审计性与研究伦理合规。

### M1 开题约束与工程现状固化
- 目标：把开题约束转化为工程可执行条目。
- 产物：
  - `docs/STEP1_CORE_CONSTRAINTS.md`
  - `docs/STEP2_PROJECT_AUDIT.md`
- 验收标准：
  - 核心问题、方法、指标、baseline、风险、冲突均有引用标注。
- 论文映射：第1章研究问题定义、第3章实验设计约束。  
  `【PDF | 页码p10 | 段落/条目#PG010L001】` `【PDF | 页码p13 | 段落/条目#PG013L001】`

### M2 数据自动化闭环（Small/Full 通用）
- 目标：自动拉取公开数据并产出 manifest、统计、数据报告。
- 产物：
  - `data/raw/real_sources/*`（本地）
  - `data/clean/real_sft_{train,dev,test}.jsonl`（本地）
  - `reports/real_dataset_summary.json`
  - `reports/real_dataset_report.md`
- 验收标准：
  - 记录来源、许可、split、seed、hash；
  - 至少 1 份论文可直接引用的数据统计表/图。
- 论文映射：第3章数据构建。  
  `【DOCX | 三、课题技术路线及研究方案 | 段落#T03R001】`

### M3 Small Real 真实训练闭环（论文主链起点）
- 目标：真实 LoRA/QLoRA 训练跑通并可复现。
- 产物：
  - `logs/.../train_log.jsonl`
  - `checkpoints/.../run_manifest.json`
  - `reports/training/...metrics.json`
  - `reports/thesis_assets/figures/loss_curve.*`
- 验收标准：
  - 出现真实 step loss（非模拟）；
  - checkpoint 可加载推理；
  - 指标表 + loss 曲线 + run card 完整。
- 论文映射：第5章训练与对齐实验。  
  `【PDF | 页码p11 | 段落/条目#PG011L001】` `【DOCX | 四、工作进度安排 | 段落#T04R001】`

### M4 评测与对比闭环（含 baseline 与消融）
- 目标：生成论文可用主结果表、对比表、消融表、案例分析。
- 产物：
  - `reports/thesis_assets/tables/*.csv`
  - `reports/sota_compare.md`
  - `reports/error_analysis.md`
- 验收标准：
  - 覆盖事实性/安全性/可用性三类指标；
  - 覆盖 SFT vs DPO/SimPO（真实/代理口径需严格标注）；
  - 至少 1 组消融与 1 组误差案例。
- 论文映射：第6章结果分析。  
  `【PPT | 页码#15 | 要点#S015H006】` `【PPT | 页码#15 | 要点#S015H007】`

### M5 Full Experiment（资源允许时）
- 目标：在 Qwen2.5-7B/14B 或 Qwen3 小模型上完成完整规模实验。
- 产物：
  - 主实验表、完整消融、资源消耗表、局限性分析。
- 验收标准：
  - 数据流程稳定；
  - Small Real 证据链已闭合；
  - 每轮仅变更 1~2 个关键变量可归因。
- 论文映射：第6章主结果与第7章局限性。  
  `【PDF | 页码p12 | 段落/条目#PG012L001】` `【PDF | 页码p14 | 段落/条目#PG014L002】`

## 2. 风险与缓解（跨里程碑）
- 技术风险：真实对齐训练器缺失。  
  - 缓解：先完成真实 SFT + 评测闭环，再替换真实 DPO/SimPO 组件。
- 算力风险：本机若无 CUDA/GPU，7B 训练不可行。  
  - 缓解：先完成脚本化自检与可迁移配置，转到可用 GPU 环境执行。
- 数据风险：医学数据许可与 PHI 风险。  
  - 缓解：仅用公开可复现数据集，强制 PII 清理与来源记录。
- 论文风险：代理结果与真实结果混写。  
  - 缓解：报告物理隔离 + 文件名口径隔离 + run card 标注训练模式。

## 3. 当前最小可执行闭环
1. 运行 M0 安全底座并提交。
2. 运行 M2 的小样本数据构建。
3. 运行 M3 的小规模真实训练（资源不足时先落盘脚本与诊断报告）。
4. 运行 M4 评测与图表导出，形成首版论文资产包。
