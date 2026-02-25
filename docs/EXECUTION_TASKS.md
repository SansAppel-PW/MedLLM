# MedLLM 可执行任务清单（基于开题报告）

## 1. 使用方式
- 状态字段：`TODO` / `DOING` / `DONE` / `BLOCKED`。
- 建议执行：每条任务建 1 个 GitHub Issue，标题使用 `任务ID + 任务名`。
- 完成标准（统一 DoD）：代码可运行、产出文件齐全、关键指标可复现、文档已更新。

## 2. 里程碑与关键路径
- M0（2025.11-2025.12）：项目基线与数据治理（`T001-T110`）。
- M1（2026.01-2026.02）：幻觉检测系统（`T201-T207`）。
- M2（2026.03）：SFT 与 DPO/SimPO 对齐训练（`T301-T306`）。
- M3（2026.04）：综合评测与消融（`T401-T407`）。
- M4（2026.05-2026.06）：Demo 与论文交付（`T501-T506`）。

关键路径：`T001 -> T101 -> T105 -> T106 -> T109 -> T301 -> T303/T304 -> T401 -> T405 -> T501`。

## 3. 可执行任务清单

| ID | 任务 | 交付物（落盘路径） | 验收标准（DoD） | 依赖 | 优先级 | 状态 |
|---|---|---|---|---|---|---|
| T001 | 初始化项目目录结构 | `src/` `scripts/` `configs/` `data/{raw,clean,kg,benchmark}` `eval/` `reports/` | 目录齐全，可直接放入后续模块 | 无 | P0 | DONE |
| T002 | 环境与依赖管理 | `pyproject.toml` 或 `requirements.txt`，`Makefile` | `make setup` 可完成环境安装 | T001 | P0 | DONE |
| T003 | 基础工程规范 | `.gitignore` `README.md` `docs/ARCH.md` | 忽略规则覆盖数据缓存/模型权重，README可引导运行 | T001 | P0 | DONE |
| T004 | 实验配置中心 | `configs/base.yaml` `configs/train/*.yaml` `configs/eval/*.yaml` | 单命令可读取配置并启动脚本 | T002 | P0 | DONE |
| T005 | 数据版本登记 | `docs/DATA_CATALOG.md` | 列出数据来源、许可、用途、更新时间 | T001 | P0 | DONE |
| T006 | 质量与安全基线 | `docs/SAFETY_POLICY.md` | 明确禁忌输出、拒答策略、免责声明 | T003 | P0 | DONE |
| T101 | 数据源接入脚本 | `scripts/data/download_datasets.sh` | 可下载并落地 MedQA/CMtMedQA 等数据 | T002,T005 | P0 | DONE |
| T102 | 数据统一 Schema | `src/data/schema.py` `data/raw/schema_examples.json` | 多来源数据转换为统一字段（query/context/answer/meta） | T101 | P0 | DONE |
| T103 | PII 清洗模块 | `src/data/pii_cleaner.py` | 能识别并脱敏姓名/电话/身份证等敏感信息 | T102 | P0 | DONE |
| T104 | 医疗 NER+EL 管线 | `src/data/ner_el_pipeline.py` | 可抽取 Disease/Drug/Symptom 并链接标准术语 | T102 | P0 | TODO |
| T105 | KG 三元组映射 | `src/data/triple_mapper.py` `data/kg/triples/*.jsonl` | 文本可稳定映射为 `<h,r,t>` 三元组 | T104 | P0 | TODO |
| T106 | KG 逻辑冲突检测 | `src/data/kg_validator.py` | 可检测禁忌症、适应症、剂量等冲突并输出标签 | T105 | P0 | TODO |
| T107 | 低置信冲突重写 | `src/data/rewrite_low_conflict.py` | 低置信冲突样本可重写并保留修正轨迹 | T106 | P1 | TODO |
| T108 | 数据清洗质量报告 | `reports/data_cleaning_report.md` | 含剔除率、冲突类型分布、样本前后对比 | T106,T107 | P0 | TODO |
| T109 | SFT 训练数据产出 | `data/clean/sft_train.jsonl` `data/clean/sft_dev.jsonl` | 可直接供训练脚本读取 | T108 | P0 | TODO |
| T110 | 偏好对候选集生成 | `data/clean/pref_seed_pairs.jsonl` | 包含 `(x,y_good,y_bad_seed)` 初始对 | T109 | P0 | TODO |
| T201 | 白盒不确定性评分 | `src/detect/whitebox_uncertainty.py` | 输出 token entropy/self-consistency/eigenscore | T109 | P0 | TODO |
| T202 | 原子事实抽取器 | `src/detect/atomic_fact_extractor.py` | 长回答可拆为原子事实列表 | T109 | P0 | TODO |
| T203 | 医疗证据检索模块 | `src/detect/retriever.py` | 支持本地库检索 Top-K 证据 | T202 | P0 | TODO |
| T204 | NLI 事实核查器 | `src/detect/nli_checker.py` | 对每条原子事实输出 entail/contradict/neutral | T203 | P0 | TODO |
| T205 | 混合风险融合引擎 | `src/detect/risk_fusion.py` | 结合白盒+黑盒输出 Low/Medium/High | T201,T204 | P0 | TODO |
| T206 | 实时拦截与告警接口 | `src/detect/runtime_guard.py` | 高风险回答可拦截并给出替代回复 | T205,T006 | P0 | TODO |
| T207 | 检测模块离线评测 | `reports/detection_eval.md` | 给出拦截率、召回率、误报率 | T205 | P0 | TODO |
| T301 | 基座 SFT 训练 | `src/train/sft_train.py` `reports/sft_baseline.md` | 产出可用 SFT baseline 模型与基线指标 | T109,T002 | P0 | TODO |
| T302 | 对抗性实体替换器 | `src/train/hard_negative_builder.py` | 能生成高语义相似但医学事实错误的 `y_bad` | T110,T106 | P0 | TODO |
| T303 | DPO 训练流水线 | `src/train/dpo_train.py` `configs/train/dpo.yaml` | 跑通 DPO 并输出 checkpoint 与日志 | T301,T302 | P0 | TODO |
| T304 | SimPO 训练流水线 | `src/train/simpo_train.py` `configs/train/simpo.yaml` | 跑通 SimPO 并输出 checkpoint 与日志 | T301,T302 | P0 | TODO |
| T305 | 可选 KTO 实验 | `src/train/kto_train.py` | 完成 KTO 对比（可选，时间不足可降级） | T301,T302 | P2 | TODO |
| T306 | 对齐训练对比报告 | `reports/alignment_compare.md` | DPO/SimPO/KTO 指标与案例对比 | T303,T304,T305 | P0 | TODO |
| T401 | 医疗幻觉评测集定稿 | `data/benchmark/med_hallu_benchmark.jsonl` | 覆盖药物/疾病/检查/禁忌等场景 | T110,T202 | P0 | TODO |
| T402 | 指标实现与脚本 | `eval/metrics.py` `scripts/eval/run_eval.sh` | 支持 FactScore/WinRate/InterceptionRate/Rouge | T401,T207 | P0 | TODO |
| T403 | 消融一：去除 KG 清洗 | `reports/ablation_kg.md` | 对比有/无 KG 清洗后的事实错误率变化 | T301,T402 | P0 | TODO |
| T404 | 消融二：检测机制对比 | `reports/ablation_detection.md` | 对比白盒/黑盒/混合三种检测效果 | T205,T402 | P0 | TODO |
| T405 | 消融三：SFT vs DPO vs SimPO | `reports/ablation_alignment.md` | 结论明确：哪种策略更优及原因 | T303,T304,T402 | P0 | TODO |
| T406 | 对标模型评测 | `reports/sota_compare.md` | 与 HuatuoGPT/BioMistral 等做统一口径对比 | T405 | P1 | TODO |
| T407 | 错误案例分析 | `reports/error_analysis.md` | 至少覆盖 30 个失败案例并分类归因 | T405 | P1 | TODO |
| T501 | 推理服务化 | `src/serve/app.py` | 提供问答+风险分级接口（REST/CLI） | T206,T304 | P0 | TODO |
| T502 | Demo 前端/交互页 | `demo/` | 能展示回答、证据片段、风险等级与拦截提示 | T501 | P1 | TODO |
| T503 | 部署与运行脚本 | `scripts/deploy/run_demo.sh` `docs/DEPLOY.md` | 一键拉起 Demo（本地或服务器） | T501,T502 | P1 | TODO |
| T504 | 端到端验收报告 | `reports/e2e_acceptance.md` | 从输入问题到风险输出全链路可复现 | T503,T402 | P0 | TODO |
| T505 | 论文图表与材料沉淀 | `reports/thesis_assets/` | 指标表、流程图、关键案例可直接入论文 | T405,T407 | P1 | TODO |
| T506 | 答辩演示素材 | `docs/defense_outline.md` `slides/` | 覆盖问题定义、方法、实验、结论、局限 | T504,T505 | P1 | TODO |

## 4. 建议先开工的 10 个任务（本周）
- `T001` `T002` `T003` `T005` `T101` `T102` `T103` `T104` `T105` `T106`

## 5. 风险与应对（执行期）
- 数据许可风险：优先完成 `T005`，未明确许可的数据不入训练集。
- 医疗安全风险：上线前必须完成 `T006` 与 `T206`，高风险问题默认拒答。
- 算力与进度风险：优先跑 7B/8B 基线，32B/235B 仅在资源允许时扩展。

