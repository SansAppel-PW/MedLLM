# 学术合规与数据来源说明

## 1. 真实来源数据
- 训练语料来自 HuggingFace 开源数据集：
  - `Suprit/CMtMedQA`
  - `FreedomIntelligence/Huatuo26M-Lite`
  - `FreedomIntelligence/huatuo_encyclopedia_qa`
- 评测题干来自 `GBaker/MedQA-USMLE-4-options-hf`。
- 采样、去重、切分过程由 `scripts/data/build_real_dataset.py` 生成并可复现。

## 2. 合成/构造数据（需在论文中显式披露）
- `real_medqa_benchmark` 的高风险样本是由真实题干上的错误选项构造而来（`incorrect_option_adversarial`），并非人工手写臆造文本。
- 偏好对中的 `rejected` 回答由规则替换/扰动生成（实体替换、数值扰动、语义翻转）。

## 3. 模拟训练（仅 Sanity 层）
- `src/train/sft_train.py`、`dpo_train.py`、`simpo_train.py`、`kto_train.py` 为离线代理实现，输出 proxy 指标。
- 这些结果仅用于工程流程验证，不可用于论文主结论。
- 论文主线训练必须使用 `src/train/real_sft_train.py`、`real_dpo_train.py`、`real_simpo_train.py`、`real_kto_train.py`。

## 4. 可接受论文表述建议
- 可写：已完成 small-real 与 real alignment（DPO/SimPO/KTO）的真实训练证据链，并形成可复现实验资产。
- 可写：当前无 GPU 环境下，Layer-B Qwen2.5-7B 主实验以 blocker 报告形式记录，迁移后可一键补齐。
- 不可写：未执行的 full-scale GPU 主实验结果，或将 proxy 表误写成真实主结果。
