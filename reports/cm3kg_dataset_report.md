# 真实数据集构建报告（CM3KG）

- 数据来源：`CM3KG/medical.csv` + `CM3KG/Disease.csv`（本地真实知识图谱数据）
- 疾病条目数：8808
- 原始三元组数：483272

## 产出规模
- 训练集：41305
- 验证集：5162
- 测试集：5162
- 幻觉评测基准（正/负）：7998
- 检索知识库条目：180000

## 产物路径
- `data/clean/cm3kg_sft_train.jsonl`
- `data/clean/cm3kg_sft_dev.jsonl`
- `data/clean/cm3kg_sft_test.jsonl`
- `data/benchmark/cm3kg_benchmark.jsonl`
- `data/kg/cm3kg_core_kb.jsonl`

## 合规说明
- CM3KG 来自公开仓库下载；发布论文前需再次核验上游许可条款与再分发限制。
