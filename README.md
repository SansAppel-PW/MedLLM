# MedLLM

面向中文医疗问答大模型的幻觉检测与缓解工程项目。

## 项目目标
- 基于真实数据构建训练集与评测集，减少 demo 级假数据依赖。
- 基于白盒不确定性 + 检索核查的混合检测，实现高风险拦截。
- 基于 SFT / DPO / SimPO 的对齐训练流程（当前仓库为轻量模拟实现），支持论文实验复现实验编排。

## 学术合规说明
- `src/train/sft_train.py`、`src/train/dpo_train.py`、`src/train/simpo_train.py`、`src/train/kto_train.py` 为代理/模拟流程。
- `src/train/real_sft_train.py` 与 `src/train/real_dpo_train.py` 为真实训练入口（含真实 forward/backward、loss、checkpoint、日志与 manifest）。
- 当前 `ALIGNMENT_MODE=real` 已支持真实 DPO；SimPO/KTO 仍为代理实现（会在报告中标注）。
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

## Repo Safety Guard（提交前强制）
```bash
# git add -A 前检查工作区候选文件
make repo-guard

# git add -A 后检查 staging 区
make repo-guard-staged
```

若 Guard 失败，先修复 `.gitignore` 或取消追踪大文件，再继续提交。

## API Key 本地注入
```bash
cp .env.example .env
# 填写 THIRD_PARTY_API_KEY，默认 THIRD_PARTY_BASE_URL 为 https://api.gptsapi.net/v1
```

## 最小数据资产自愈（缺失时自动生成）
```bash
make bootstrap-data
```

输出：
- `data/raw/schema_examples.json`
- `data/kg/cmekg_demo.jsonl`
- `data/benchmark/med_hallu_benchmark.jsonl`
- `reports/data_bootstrap_report.md`
- `reports/data_bootstrap_manifest.json`

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

## 真实数据自愈（自治循环优先使用）
```bash
make ensure-real-data
```

说明：
- 当 `real_sft_{train,dev,test}.jsonl` 不存在或样本量低于阈值时自动重建；
- 默认使用中等规模采样参数，避免每轮循环都全量抓取。

## 训练对齐流水线（真实数据）
```bash
# 默认：真实 SFT + 代理 DPO/SimPO/KTO（ALIGNMENT_MODE=proxy）
bash scripts/train/run_real_alignment_pipeline.sh
```

输出：
- `checkpoints/layer_b/qwen25_7b_sft/`
- `logs/layer_b/qwen25_7b_sft/train_log.jsonl`
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`
- `reports/training/{dpo,simpo,kto}_metrics.json`
- `reports/alignment_compare.md`

说明：
- `ALIGNMENT_MODE=proxy`：DPO/SimPO/KTO 使用代理训练器（当前默认）。
- `ALIGNMENT_MODE=real`：执行真实 DPO（带回退），SimPO/KTO 暂保持代理。

## Layer-B 真实 SFT（论文主链起点）
```bash
bash scripts/train/run_layer_b_real_sft.sh
```

输出：
- `checkpoints/layer_b/qwen25_7b_sft/`
- `checkpoints/layer_b/qwen25_7b_sft/run_manifest.json`
- `logs/layer_b/qwen25_7b_sft/train_log.jsonl`
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`

## Layer-B Qwen7B 自动回退训练（OOM 自愈）
```bash
bash scripts/train/run_layer_b_qwen_autofallback.sh
```

行为：
- 有 GPU：自动按 3 档参数尝试（2048/16 -> 1536/32 -> 1024/64）。
- 无 GPU：写出阻塞报告 `reports/small_real/qwen_layer_b_blocker.md`，并退出 0（不阻塞其余流程）。

## Small Real 一键闭环（prepare -> train -> eval -> visualize -> run_card）
```bash
# 默认先尝试 Qwen2.5-0.5B，失败自动回退到本地 tiny-gpt2 缓存
bash scripts/train/run_small_real_pipeline.sh
```

输出（默认 `RUN_TAG=small_real_lora_v3`）：
- `checkpoints/small_real/<RUN_TAG>/run_manifest.json`
- `logs/small_real/<RUN_TAG>/train_log.jsonl`
- `reports/training/<RUN_TAG>_metrics.json`
- `reports/small_real/<RUN_TAG>/eval_metrics.{json,csv}`
- `reports/small_real/<RUN_TAG>/loss_curve.{csv,png,pdf}`
- `reports/small_real/<RUN_TAG>/run_card.{json,md}`

## 自治循环（单轮）
```bash
RUN_TAG=small_real_lora_v6 bash scripts/run_autonomous_iteration.sh
# 或
bash scripts/run_autonomous_iteration.sh
make loop-once
```

默认行为：
- 先执行 Repo Guard；
- 先自愈真实数据（缺失时自动抓取）；
- 再跑 small-real 闭环；
- 再尝试 Qwen7B Layer-B（无 GPU 时写 blocker）；
- 再执行 real alignment（默认 `ALIGNMENT_MODE=real` 且 `SKIP_LAYER_B=1`，避免重复 Layer-B 开销）；
- 最后自动生成 baseline 审计表、iteration 报告、decision log 和 thesis-ready 汇总包。

Decision log 单独更新：
```bash
make decision-log
```

## 论文写作资产汇总
```bash
make thesis-ready
```

输出：
- `reports/thesis_assets/tables/main_results_small_real.csv`
- `reports/thesis_assets/tables/main_results_real.csv`
- `reports/thesis_assets/tables/main_results_proxy.csv`
- `reports/thesis_assets/tables/main_results_dual_view.md`
- `reports/thesis_assets/tables/baseline_real_mainline.csv`
- `reports/thesis_assets/tables/baseline_proxy_background.csv`
- `reports/thesis_assets/tables/baseline_audit_dual_view.md`
- `reports/thesis_assets/tables/ablation_small_real_runs.csv`
- `reports/thesis_assets/thesis_ready_summary.md`
- `reports/thesis_assets/thesis_ready_summary.json`

## 真实对齐消融（DPO beta）
```bash
make dpo-ablation
```

输出：
- `reports/thesis_assets/tables/dpo_beta_ablation.csv`
- `reports/thesis_assets/tables/dpo_beta_ablation.json`
- `reports/dpo_beta_ablation.md`

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
# 或
make task-audit
```

## 开题一致性审计（框架/流程/指标/基线对齐）
```bash
python scripts/audit/check_opening_alignment.py
# 或
make opening-audit
```

## 回归测试
```bash
pytest -q tests
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
