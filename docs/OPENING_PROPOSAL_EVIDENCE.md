# 开题材料结构化证据提取（阶段0）

## 0. 来源文件与抽取产物
- 原始文件：
  - `开题报告-胡佩文.pdf`
  - `开题报告-胡佩文.docx`
  - `开题报告-胡佩文.pptx`
- 全文抽取：
  - `tmp/docs/开题报告-胡佩文.pdf.txt`
  - `tmp/docs/开题报告-胡佩文.docx.txt`
  - `tmp/docs/开题报告-胡佩文.pptx.txt`

## 1. PDF 结构化关键信息
### 1.1 课题定位与总目标
- 目标是构建“可信、可控、可溯源”的中文医疗问答大模型。[PDF: PG003L007]
- 核心治理框架是“数据治理（事前）-实时检测（事中）-模型对齐（事后）”三层闭环。[PDF: PG010L001]

### 1.2 技术路线与方法
- 数据侧：NER+EL、三元组映射、CMeKG/UMLS 冲突校验、分级清洗与重写。[PDF: PG010L001]
- 检测侧：白盒不确定性（Entropy/Self-Consistency/EigenScore）+ 黑盒 RAG/NLI 事实核查。[PDF: PG010L001]
- 训练侧：SFT + DPO/SimPO/KTO，对抗性困难负样本是重点。[PDF: PG011L001]

### 1.3 Baseline 与对比对象
- 文献与对比对象覆盖 Med-PaLM 2、HuatuoGPT、BioMistral、ChatDoctor 等。[PDF: PG005L001][PDF: PG007L001][PDF: PG008L001]
- 基座候选为 Qwen-2.5-7B/14B-Instruct、Llama-3-8B-Instruct；HuatuoGPT-II、BioMistral 作为对比基座。[PDF: PG012L001]

### 1.4 评测与交付
- 指标包括 FactScore、Win Rate（GPT-4 Judge）、Rouge-L 及消融（SFT vs DPO vs SimPO、有无 KG 清洗）。[PDF: PG013L001]
- 预期成果包括：清洗脚本库、低幻觉模型 Demo、评测基准、硕士论文。[PDF: PG014L002]

### 1.5 资源与进度
- 算力假设为 A100/A800 集群或租赁资源。[PDF: PG013L001]
- 里程碑：2025.11-2026.06（文献/数据、检测、训练、评测、论文）。[PDF: PG013L001]

## 2. DOCX 结构化关键信息
### 2.1 题目与任务定义
- 题目明确围绕“数据清洗 + 偏好对齐 + 幻觉检测缓解”。[DOCX: P0004]
- 摘要重复强调三层系统方案与对抗性偏好对齐路线。[DOCX: T01R005]

### 2.2 研究内容与难点
- 难点聚焦：
  - 高隐蔽性医疗幻觉识别。
  - 高质量对抗性负样本自动构建。
  - 长上下文/多轮对话下事实一致性维持。[DOCX: T03R001]

### 2.3 方法与实验设计
- 明确 SFT、DPO、SimPO、KTO 对比，强调 LoRA 或全量微调可选。[DOCX: T03R001]
- 明确使用 FactScore/WinRate/Rouge-L 与 SOTA 对比、消融评估。[DOCX: T04R001]

## 3. PPT 结构化关键信息
### 3.1 面向答辩表达的技术主线
- 强调“白盒+黑盒”混合检测和“对抗性实体替换”DPO 的创新叙事。[PPT: S011H002][PPT: S012H002][PPT: S018H006]
- 明确提出 KG 校验有效性与混合检测互补性的消融实验设计。[PPT: S015H007]

### 3.2 实验与模型表达
- PPT 中写到模型示例含 “Qwen-32B/235B、Llama-3-8B”。[PPT: S015H005]
- 指标层面与 PDF/DOCX 一致：FactScore、Win Rate、Rouge-L、拦截率等。[PPT: S015H006]

## 4. 面向项目实施的硬约束归纳
- 必须形成数据治理、检测、对齐三层可运行闭环，不能只做单点模块。[PDF: PG010L001]
- 必须存在偏好对齐训练且对比 DPO/SimPO/KTO，不可只做 SFT。[PDF: PG011L001]
- 必须进行消融与基线对比，指标包含事实性、安全性、可用性三类。[PDF: PG013L001][PPT: S015H006][PPT: S015H007]
- 必须有清晰的阶段产出与最终论文交付物，不能停留在概念验证。[PDF: PG014L002]

## 5. 论文逻辑疑点与不一致点（需后续确认）
1. 模型规模不一致：PDF/DOCX 主方法写 Qwen-2.5-7B/14B 与 Llama-3-8B；PPT 出现 Qwen-32B/235B。需统一主实验规模与算力预算口径。[PDF: PG012L001][PPT: S015H005]
2. 任务目标与成果措辞冲突：PDF“预期成果”仍包含“Demo”表述，需在论文主线中明确“工程系统 + 真实实验证据”为主体，Demo 仅作为展示层。[PDF: PG014L002]
3. 数据来源口径有泛化风险：技术路线写了 MedMCQA/PubMedQA/Google Search API 等，当前代码与数据目录尚未体现完整落地证据，后续需给出实际启用清单与未启用原因。[PDF: PG012L001]
4. Win Rate 使用 GPT-4 Judge 与本地可复现实验之间存在可复现实验门槛差异，需定义可替代本地裁判方案或保留 API 版本与缓存证据。[PDF: PG013L001]
5. SimPO 公式在 PDF 文本抽取中存在乱码，正式论文中需校对公式排版与符号一致性。[PDF: PG012L001][PDF: PG013L001]
