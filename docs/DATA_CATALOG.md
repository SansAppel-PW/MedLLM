# 数据目录与许可登记

## 1. 外部真实数据源（HuggingFace）

| 数据集 | 规模（官方/采样） | 用途 | 许可 | 接入方式 | 本地产物 |
|---|---:|---|---|---|---|
| `Suprit/CMtMedQA` | 68,023 / 8,000 | 中文医疗问答训练语料 | MIT | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/cmtmedqa.jsonl` |
| `FreedomIntelligence/Huatuo26M-Lite` | 177,703 / 6,000 | 中文医疗问答训练语料 | Apache-2.0 | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/huatuo26m_lite.jsonl` |
| `FreedomIntelligence/huatuo_encyclopedia_qa` | 362,420 / 6,000 | 医学百科问答训练语料 | Apache-2.0 | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/huatuo_encyclopedia.jsonl` |
| `GBaker/MedQA-USMLE-4-options-hf` (train) | train / 6,000 | 医学考试问答训练补充语料 | CC-BY-SA-4.0 | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/medqa_usmle_train.jsonl` |
| `GBaker/MedQA-USMLE-4-options-hf` | train/val/test | 构建真实 benchmark 与参考 KB | CC-BY-SA-4.0 | `scripts/data/build_real_dataset.py` | `data/benchmark/real_medqa_benchmark.jsonl` |
| `CM3KG`（本地导入） | 8k+ disease / 6k+ symptom | 构建 CMeKG 风格知识图谱基础设施 | 见上游仓库说明 | `scripts/data/build_cmekg_from_cm3kg.py` | `data/kg/cmekg_integrated.jsonl` |

## 2. 项目衍生数据产物

| 数据产物 | 说明 | 生成脚本 |
|---|---|---|
| `data/clean/real_sft_train.jsonl` | 真实 SFT 训练集（去重后切分） | `scripts/data/build_real_dataset.py` |
| `data/clean/real_sft_dev.jsonl` | 真实 SFT 验证集 | `scripts/data/build_real_dataset.py` |
| `data/clean/real_sft_test.jsonl` | 真实 SFT 测试集 | `scripts/data/build_real_dataset.py` |
| `data/clean/real_pref_seed_pairs.jsonl` | 真实偏好对种子数据 | `scripts/train/run_real_alignment_pipeline.sh` |
| `data/kg/real_medqa_reference_kb.jsonl` | 基于 benchmark 正例构建的参考知识库 | `scripts/data/build_benchmark_reference_kb.py` |
| `data/kg/cmekg_integrated.jsonl` | 由 CM3KG 构建并融合 guardrail 三元组的集成 KG | `scripts/data/build_cmekg_from_cm3kg.py` |
| `reports/real_dataset_summary.json` | 真实数据构建统计摘要 | `scripts/data/build_real_dataset.py` |

## 3. 合规与使用规则
- 仅在遵循各数据集 License 前提下用于研究与论文实验。
- 默认不提交大体量原始/中间数据到 Git；通过脚本可复现。
- 若用于公开发布模型或商用，请再次核验上游许可条款与署名要求。
