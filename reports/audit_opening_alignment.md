# 开题要求一致性审计报告

| 模块 | 检查项 | 状态 | 证据 | 修复/动作 |
|---|---|---|---|---|
| 数据源 | CMtMedQA 数据源 | PASS | reports/real_dataset_summary.json 包含 `Suprit/CMtMedQA` | 保持 |
| 数据源 | Huatuo-26M-Lite 数据源 | PASS | reports/real_dataset_summary.json 包含 `FreedomIntelligence/Huatuo26M-Lite` | 保持 |
| 数据源 | MedQA 数据源 | PASS | benchmark 文件存在并由 MedQA 构建: `data/benchmark/real_medqa_benchmark.jsonl` | 如需将 MedQA 纳入 SFT，重跑 build_real_dataset.py --medqa-count |
| 数据源 | CM3KG 本地知识图谱目录 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/CM3KG` | 保持或迁移到 GPU 环境后同路径挂载 |
| 知识图谱 | 集成 CMeKG 文件 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/data/kg/cmekg_integrated.jsonl` | 执行 scripts/data/build_cmekg_from_cm3kg.py |
| 检测/RAG | 原子事实抽取 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/src/detect/atomic_fact_extractor.py` | 保持 |
| 检测/RAG | 检索模块 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/src/detect/retriever.py` | 保持 |
| 检测/RAG | NLI核查 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/src/detect/nli_checker.py` | 保持 |
| 检测/RAG | 运行时守卫 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/src/detect/runtime_guard.py` | 保持 |
| 训练 | 真实 SFT 入口 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/src/train/real_sft_train.py` | 保持 |
| 训练 | 真实偏好对齐入口 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/src/train/real_pref_train.py` | 保持 |
| 训练 | 对齐编排脚本 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/scripts/train/run_real_alignment_pipeline.sh` | 保持 |
| 训练 | SFT 指标 | PASS | 存在 train_loss: `/Users/bibo/Desktop/MedLLM_codex/reports/training/layer_b_qwen25_7b_sft_metrics.json` | 指标已可用于论文 |
| 训练 | DPO 指标 | PASS | 真实训练指标: `/Users/bibo/Desktop/MedLLM_codex/reports/training/dpo_metrics.json` | 指标已可用于论文 |
| 训练 | SimPO 指标 | PASS | 真实训练指标: `/Users/bibo/Desktop/MedLLM_codex/reports/training/simpo_metrics.json` | 指标已可用于论文 |
| 训练 | KTO 指标 | PASS | 真实训练指标: `/Users/bibo/Desktop/MedLLM_codex/reports/training/kto_metrics.json` | 指标已可用于论文 |
| 论文产物 | 数据报告 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/reports/real_dataset_report.md` | 保持 |
| 论文产物 | 清洗报告 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/reports/data_cleaning_report.md` | 保持 |
| 论文产物 | 综合评测 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/reports/eval_default.md` | 保持 |
| 论文产物 | SOTA 对比 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/reports/sota_compare.md` | 保持 |
| 论文产物 | 论文草稿材料 | PASS | 存在: `/Users/bibo/Desktop/MedLLM_codex/reports/thesis_support/thesis_draft_material.md` | 保持 |

## 汇总
- PASS: 21
- WARN: 0
- FAIL: 0

## 结论
- 若 FAIL=0 且关键训练指标为真实口径，则可进入论文写作主线。
- 若存在 WARN，需在论文中如实标注限制条件与后续补实验计划。
