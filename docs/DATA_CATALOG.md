# 数据目录与许可登记

## 1. 外部真实数据源（HuggingFace）

| 数据集 | 规模（官方/采样） | 用途 | 许可 | 接入方式 | 本地产物 |
|---|---:|---|---|---|---|
| `Suprit/CMtMedQA` | 68,023 / 按参数采样 | 中文医疗问答训练语料 | MIT | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/cmtmedqa.jsonl` |
| `FreedomIntelligence/Huatuo26M-Lite` | 177,703 / 按参数采样 | 中文医疗问答训练语料 | Apache-2.0 | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/huatuo26m_lite.jsonl` |
| `FreedomIntelligence/huatuo_encyclopedia_qa` | 362,420 / 按参数采样 | 医学百科问答训练语料 | Apache-2.0 | `scripts/data/build_real_dataset.py` | `data/raw/real_sources/huatuo_encyclopedia.jsonl` |
| `GBaker/MedQA-USMLE-4-options-hf` | train/val/test | 构建真实 benchmark 与参考 KB | CC-BY-SA-4.0 | `scripts/data/build_real_dataset.py` | `data/benchmark/real_medqa_benchmark_from_hf.jsonl` |

## 1.1 本地真实知识图谱数据源（CM3KG）

| 数据源 | 规模 | 用途 | 许可 | 接入方式 | 本地产物 |
|---|---:|---|---|---|---|
| `CM3KG/medical.csv` | 8,808 疾病条目 | 构建真实 SFT 训练语料与 benchmark 正负样本 | 需核验上游条款 | `scripts/data/build_cm3kg_real_assets.py` | `data/clean/real_sft_*.jsonl`, `data/benchmark/real_medqa_benchmark.jsonl` |
| `CM3KG/Disease.csv` | 483,272 三元组 | 构建检索知识库与 KG 一致性校验基础 | 需核验上游条款 | `scripts/data/build_cm3kg_real_assets.py` | `data/kg/cm3kg_core_kb.jsonl` |

## 2. 项目衍生数据产物

| 数据产物 | 说明 | 生成脚本 |
|---|---|---|
| `data/clean/real_sft_train.jsonl` | 统一真实 SFT 训练集（CM3KG + 外部问答） | `scripts/data/build_unified_real_assets.py` |
| `data/clean/real_sft_dev.jsonl` | 统一真实 SFT 验证集 | `scripts/data/build_unified_real_assets.py` |
| `data/clean/real_sft_test.jsonl` | 统一真实 SFT 测试集 | `scripts/data/build_unified_real_assets.py` |
| `data/clean/real_pref_seed_pairs.jsonl` | 真实偏好对种子数据 | `scripts/train/run_real_alignment_pipeline.sh` |
| `data/kg/real_medqa_reference_kb.jsonl` | 基于 benchmark 正例构建的参考知识库 | `scripts/data/build_benchmark_reference_kb.py` |
| `data/kg/cm3kg_core_kb.jsonl` | 基于 CM3KG 构建的核心检索 KG | `scripts/data/build_cm3kg_real_assets.py` |
| `data/kg/real_medqa_reference_kb_merged.jsonl` | benchmark KB + CM3KG KB 合并知识库 | `scripts/eval/run_thesis_pipeline.sh` |
| `reports/real_dataset_summary.json` | 真实数据构建统计摘要 | `scripts/data/build_cm3kg_real_assets.py` / `scripts/data/build_real_dataset.py` |
| `reports/hf_real_dataset_summary.json` | 外部问答数据构建摘要（Huatuo/CMt/MedQA） | `scripts/data/build_real_dataset.py` |
| `reports/cm3kg_dataset_summary.json` | CM3KG 构建摘要 | `scripts/data/build_cm3kg_real_assets.py` |
| `data/benchmark/real_medqa_benchmark.jsonl` | 统一 benchmark（MedQA + CM3KG） | `scripts/data/build_unified_real_assets.py` |

## 3. 合规与使用规则
- 仅在遵循各数据集 License 前提下用于研究与论文实验。
- 默认不提交大体量原始/中间数据到 Git；通过脚本可复现。
- 若用于公开发布模型或商用，请再次核验上游许可条款与署名要求。
