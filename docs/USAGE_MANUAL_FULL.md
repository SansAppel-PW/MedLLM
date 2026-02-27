# MedLLM 全量使用说明（GPU 一键复现实验版）

## 1. 文档目标
本说明用于保证你在 GPU 租赁环境中“迁移代码后一键执行”，并拿到论文所需的完整实验产物。

## 2. 当前项目状态（2026-02-27）
- 迁移就绪：`reports/migration/handoff_readiness.json` -> `ready=true`
- 严格完工：`reports/migration/gpu_completion_check.json` -> `strict_pass=false`
- 原因：当前机器无 CUDA，真实 Qwen2.5-7B/14B 训练尚未执行，仅保留跳过证据。

这意味着：
- 工程链路完整；
- 只差 GPU 上执行真实训练闭环。

## 3. 仓库结构（主链）
- `src/`：核心模块（数据治理、检测、训练、服务）
- `scripts/data/`：真实数据构建与治理
- `scripts/train/`：Layer-B SFT + DPO/SimPO/KTO 编排
- `scripts/eval/`：评测、鲁棒性审计、论文资产生成
- `scripts/migration/`：GPU 迁移、环境 bootstrap、严格完工校验
- `reports/`：所有实验证据、图表、报告
- `docs/`：运行手册与系统文档

## 4. 环境准备

### 4.1 基础依赖
- Python >= 3.10
- Git
- 可选：CUDA 驱动 + 对应 PyTorch GPU wheel（GPU 环境）

### 4.2 安装依赖
```bash
make setup
```
或
```bash
python3 -m pip install -r requirements.txt
```

### 4.3 API 评测配置
根目录 `.env`：
```env
OPENAI_BASE_URL=https://api.gptsapi.net/v1
OPENAI_API_KEY=***
```

说明：
- 当开启 `LLM Judge / LLM 风险评测 / v2 LLM 回退` 时，必须有 `.env` 或环境变量 `OPENAI_API_KEY`。

## 5. 本地快速验证（无 GPU）
### 5.1 一键论文流水线（允许训练跳过）
```bash
make paper-ready
```

### 5.2 关键状态文件
- `reports/pipeline/paper_ready_status.md`
- `reports/thesis_support/thesis_readiness.md`
- `reports/training/resource_skip_report.md`

## 6. GPU 迁移与一键执行（核心）

### 6.1 迁移前生成交接清单
```bash
make gpu-manifest
```
产出：
- `reports/migration/gpu_handoff_manifest.json`
- `reports/migration/gpu_handoff_manifest.md`

### 6.2 GPU 机器环境安装
```bash
make gpu-bootstrap
```

### 6.3 一键真实实验（严格模式）
```bash
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" \
MODEL_TIER="7b" \
ALLOW_SKIP_TRAINING=false \
FORCE_SKIP_TRAINING=false \
make gpu-run
```

默认行为：
- 强制检查 CUDA；
- 运行真实 SFT + 真实偏好对齐；
- 运行 thesis 评测与资产构建；
- 执行严格完工校验。

### 6.4 GPU 后完工确认
```bash
make gpu-complete-check
```

成功标准：
- `reports/migration/gpu_completion_check.json` 中 `strict_pass=true`
- `reports/thesis_support/thesis_readiness.json` 中 `ready_for_writing=true`

### 6.5 Day1 单文件脚本（零思考执行）
```bash
bash day1_run.sh
# 或
make day1-run
```

脚本会顺序执行：
1. 同步分支并拉取最新代码
2. GPU/环境检查与 `make gpu-bootstrap`
3. `make gpu-check` 与 GPU-run dry-run
4. 真实 `make gpu-run`（可由 `DAY1_DRY_RUN=true` 跳过）
5. `make gpu-complete-check` 严格完工校验
6. 生成 `reports/migration/day1_run_summary.md`

## 7. 主要命令清单

### 数据
```bash
python3 scripts/data/build_real_dataset.py
python3 scripts/data/run_data_governance_pipeline.py
```

### 训练
```bash
bash scripts/train/run_real_alignment_pipeline.sh
bash scripts/train/run_layer_b_real_sft.sh
```

### 评测
```bash
bash scripts/eval/run_thesis_pipeline.sh
bash scripts/eval/run_detection_robustness.sh
```

### 迁移
```bash
python3 scripts/migration/check_handoff_readiness.py
python3 scripts/migration/check_gpu_completion.py
bash scripts/migration/run_gpu_thesis_experiment.sh
```

## 8. 输出物与论文映射
- 数据与清洗：`reports/real_dataset_report.md`、`reports/data_cleaning_report.md`
- 训练与资源：`reports/training/*.json`、`reports/training/resource_preflight.json`
- 检测评测：`reports/detection_eval*.md`
- 综合评测：`reports/eval_default.md`、`reports/sota_compare.md`
- 论文资产：`reports/thesis_assets/`
- 论文材料：`reports/thesis_support/thesis_draft_material.md`
- 完备度审计：`reports/thesis_support/thesis_readiness.md`

## 9. 常见问题

### 9.1 CUDA OOM
- 脚本内置自动降级（减小 batch、增大 grad accumulation、开启 gradient checkpointing）。
- 仍失败时检查显存、模型 tier、是否混用其他进程。

### 9.2 strict_pass=false
优先检查：
1. `reports/training/layer_b_qwen25_7b_sft_metrics.json` 是否 `skipped=false`
2. `checkpoints/layer_b/qwen25_7b_sft/final` 是否存在
3. `reports/training/{dpo,simpo,kto}_metrics.json` 是否 `skipped=false`
4. `checkpoints/{dpo-real-baseline,simpo-real-baseline,kto-real-baseline}/final` 是否存在

### 9.3 API 调用失败
- 确认 `.env` 中 `OPENAI_BASE_URL`、`OPENAI_API_KEY`。
- 或显式关闭 API 评测开关。

## 10. 最终执行建议
在 GPU 上只需要执行三条命令：
```bash
make gpu-bootstrap
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" MODEL_TIER="7b" ALLOW_SKIP_TRAINING=false FORCE_SKIP_TRAINING=false make gpu-run
make gpu-complete-check
```

若第三条返回通过，即可进入论文最终写作与答辩准备。
