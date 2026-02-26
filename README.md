# MedLLM

面向中文医疗问答大模型的幻觉检测与缓解工程项目。

## 项目目标
- 基于真实数据构建训练集与评测集，减少 demo 级假数据依赖。
- 基于白盒不确定性 + 检索核查的混合检测，实现高风险拦截。
- 基于 SFT / DPO / SimPO / KTO 的对齐训练流程，支持真实训练与资源受限降级编排。

## 学术合规说明
- `src/train/real_sft_train.py` 为真实 SFT 训练入口（真实 forward/backward、loss、checkpoint、日志与实验清单）。
- `src/train/real_pref_train.py` 为真实 DPO/SimPO/KTO 训练入口（真实 backward、checkpoint、日志）。
- 在资源不足时，训练流水线会自动生成 `skipped` 证据并继续执行其余模块，避免流程中断。
- 若论文需要声明“完成 SFT/DPO/SimPO 实训”，需额外运行真实训练（含模型权重、loss 曲线、checkpoint 与推理复现）。
- `reports/sota_compare.md` 为“代理复现实验”，不可表述为官方 HuatuoGPT/BioMistral 完整能力对比。

## 目录结构
- `src/`: 核心代码（数据、检测、训练、服务）
- `scripts/`: 数据构建、训练、评测、审计脚本
- `configs/`: 训练与评测配置
- `data/`: 原始数据、清洗数据、KG 中间产物、评测集
- `eval/`: 综合评测逻辑
- `reports/`: 实验与分析报告
- `docs/`: 架构文档、数据登记、安全策略、执行清单

## 环境准备
```bash
make setup
```

## API 评测环境变量
项目支持 `LLM-as-a-Judge` 自动评测，使用 `python-dotenv` 从根目录 `.env` 读取：

```env
OPENAI_BASE_URL=https://api.gptsapi.net/v1
OPENAI_API_KEY=your_key_here
```

运行评测时开启：

```bash
ENABLE_LLM_JUDGE=true JUDGE_MODEL=gpt-4o-mini bash scripts/eval/run_eval.sh
```

## 真实数据构建（论文实验）
```bash
python scripts/data/build_real_dataset.py \
  --seed 42 \
  --cmt-count 8000 \
  --h26-count 6000 \
  --henc-count 6000 \
  --bench-train 1200 \
  --bench-val 300 \
  --bench-test 300
```

输出：
- `data/clean/real_sft_{train,dev,test}.jsonl`
- `data/benchmark/real_medqa_benchmark.jsonl`
- `reports/real_dataset_report.md`

## 训练对齐流水线（真实数据）
```bash
# 默认：优先真实训练（ALIGNMENT_MODE=real），资源不足自动跳过训练并继续后续模块
bash scripts/train/run_real_alignment_pipeline.sh
```

输出：
- `checkpoints/layer_b/qwen25_7b_sft/`
- `logs/layer_b/qwen25_7b_sft/train_log.jsonl`
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`
- `reports/training/{dpo,simpo,kto}_metrics.json`
- `reports/alignment_compare.md`

说明：
- `ALIGNMENT_MODE=real`：真实 DPO/SimPO/KTO（默认）。
- `ALIGNMENT_MODE=proxy`：使用代理训练器，适合快速方法学验证。
- 资源保护开关：
  - `ALLOW_SKIP_TRAINING=true`：训练失败或资源不足时自动跳过训练并继续流程（默认）。
  - `FORCE_SKIP_TRAINING=true`：强制跳过训练，仅推进其余模块。
  - 资源报告输出：`reports/training/resource_preflight.json`。

## Layer-B 真实 SFT（论文主链起点）
```bash
bash scripts/train/run_layer_b_real_sft.sh
```

输出：
- `checkpoints/layer_b/qwen25_7b_sft/`
- `checkpoints/layer_b/qwen25_7b_sft/run_manifest.json`
- `logs/layer_b/qwen25_7b_sft/train_log.jsonl`
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`

## 一键论文流水线（推荐）
```bash
make paper-ready
```

该入口串联：
- 真实数据构建（缺失时自动补齐）
- 训练对齐流水线（资源不足自动降级）
- 论文评测与资产构建
- Demo 端到端验收

状态总览输出：`reports/pipeline/paper_ready_status.md`。

## 评测与论文资产流水线
```bash
PYTHONUNBUFFERED=1 \
KB_SOURCE_SPLITS=train EVAL_SPLITS=validation,test \
DET_MAX=0 EVAL_MAX=1200 SOTA_MAX=1800 LOG_EVERY=400 \
bash scripts/eval/run_thesis_pipeline.sh
```

说明：
- 默认以 `train` split 构建参考 KB，并在 `validation,test` split 上评测，避免同集构建-评测泄漏。

输出：
- `reports/detection_eval.md`
- `reports/eval_default.md`
- `reports/ablation_*.md`
- `reports/sota_compare.md`
- `reports/error_analysis.md`
- `reports/thesis_assets/`

## 任务审计（开题任务对齐）
```bash
python scripts/audit/check_task_completion.py
```

## 回归测试
```bash
python -m pytest -q tests/test_runtime_guard_regression.py tests/test_reference_kb_split_guard.py
```

## Demo
```bash
# CLI / API / Web
scripts/deploy/run_demo.sh
scripts/deploy/run_demo.sh --api
scripts/deploy/run_demo.sh --web
```

## 当前执行清单
- `docs/EXECUTION_TASKS.md`
- `docs/RESOURCE_AWARE_EXECUTION.md`
