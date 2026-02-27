# 真实数据集构建报告（统一版）

## 来源覆盖
- CMeKG/CM3KG: 已接入（用于 KG 与结构化医学事实样本）
- Huatuo-26M/CMtMedQA: 已接入（用于真实医疗问答 SFT）
- MedQA: 已接入（用于 benchmark 与事实核验评测）

## 组成规模
- CM3KG 组件（train/dev/test）: 41305/5162/5162
- 外部问答组件（train/dev/test）: 28749/3593/3593
- 最终训练集（train/dev/test）: 70054/8755/8755

## Benchmark
- MedQA benchmark 条目: 5000
- CM3KG benchmark 条目: 7998
- 合并 benchmark 条目: 12998

## 原始文件规模（data/raw/real_sources）
- cmtmedqa.jsonl: 12000
- huatuo26m_lite.jsonl: 12000
- huatuo_encyclopedia.jsonl: 12000
- merged_real_qa.jsonl: 35935
