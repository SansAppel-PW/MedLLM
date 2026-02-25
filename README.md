# MedLLM

面向中文医疗问答大模型的幻觉检测与缓解工程项目。

## 项目目标
- 基于知识图谱的数据清洗，降低训练语料事实错误。
- 基于不确定性 + RAG 的混合检测，识别并拦截高风险幻觉输出。
- 基于 DPO/SimPO 的偏好对齐，降低模型生成医学事实错误的概率。

## 目录结构
- `src/`: 核心代码（数据、检测、训练、服务）
- `scripts/`: 数据、评测、部署脚本
- `configs/`: 训练与评测配置
- `data/`: 原始数据、清洗数据、KG 中间产物、评测集
- `eval/`: 指标与评测逻辑
- `reports/`: 实验与分析报告
- `docs/`: 架构文档、数据登记、安全策略、执行清单

## 快速开始
```bash
make setup
```

## 通过配置启动任务
```bash
make run-config CONFIG=configs/train/sft.yaml
```

## 运行数据治理流水线（T104-T110）
```bash
python scripts/data/run_data_governance_pipeline.py \
  --input data/raw/schema_examples.json \
  --kg data/kg/cmekg_demo.jsonl
```

## 运行幻觉检测评测（T201-T207）
```bash
python -m src.detect.evaluate_detection \
  --benchmark data/benchmark/med_hallu_benchmark.jsonl \
  --kg data/kg/cmekg_demo.jsonl
```

## 当前执行清单
- 见 `docs/EXECUTION_TASKS.md`
