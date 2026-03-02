# GPU Migration Runbook

本文件用于把当前仓库迁移到 GPU 租赁环境后直接执行论文主实验。

## 1. 目标
- 在 GPU 环境补齐 Layer-B Qwen2.5-7B 主实验。
- 自动串联 real alignment（DPO/SimPO/KTO）与评测产物。
- 输出可审计闭环并将 `A10` 从 `PARTIAL` 提升到 `PASS`。

## 2. 迁移前（本机）
```bash
make gpu-readiness
make gpu-mainline-dryrun
```

验收：
- `reports/gpu_migration_readiness.md` 状态应为 `READY_FOR_GPU_MAINLINE`。
- `reports/interface_consistency_audit.md` 应为 `FAIL=0`（由主线脚本自动执行）。

## 3. GPU 环境执行
```bash
python -m pip install -r requirements.txt
make gpu-mainline
```

V100-32GB（双卡）推荐：
```bash
NUM_GPUS=2 USE_TORCHRUN=1 BF16=false FP16=true make gpu-mainline
```

等价命令：
```bash
PYTHON_BIN=.venv/bin/python bash scripts/train/run_gpu_thesis_mainline.sh
```

可选开启 Judge：
```bash
ENABLE_LLM_JUDGE=1 JUDGE_MODEL=gpt-4o-mini make gpu-mainline
```

计时敏感场景（推荐一条命令收齐产物）：
```bash
NUM_GPUS=2 USE_TORCHRUN=1 BF16=false FP16=true \
ENABLE_LLM_JUDGE=0 \
AUTO_SHUTDOWN=0 \
bash scripts/deploy/run_gpu_once_harvest.sh
```
说明：
- 自动执行 `day1_run.sh` 主线；
- 自动刷新 `thesis-ready` 与可视化图表；
- 自动打包 `exports/thesis_bundle_gpu_once_<ts>.tar.gz`（含 sha256 清单）；
- 可设置 `AUTO_SHUTDOWN=1` 完成后自动关机。

## 4. 结果验收
```bash
make gpu-closure
make opening-audit
make thesis-ready
```

关键文件：
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`
- `reports/opening_alignment_audit.md`
- `reports/thesis_assets/thesis_ready_summary.md`
- `reports/gpu_experiment_closure.md`

## 5. 通过标准
- `reports/gpu_experiment_closure.md` 中全部 `PASS`。
- `reports/opening_alignment_audit.md` 中 `A10=PASS`，整体 `FAIL=0`。
- 主结果表包含 Layer-B 行：`reports/thesis_assets/tables/main_results_real.csv`。

## 6. 回传与核验
```bash
# 回传单文件归档（推荐）
rsync -avz --progress <remote>:/root/autodl-tmp/MedLLM_codex_worktree-gpt-prompt/exports/thesis_bundle_gpu_once_<ts>.tar.gz ./

# 或回传目录
rsync -avz --progress <remote>:/root/autodl-tmp/MedLLM_codex_worktree-gpt-prompt/exports/thesis_bundle_gpu_once_<ts>/ ./
```

核验：
- `bundle_manifest.json` 与 `artifact_index.csv` 中 sha256；
- `reports/thesis_assets/figures/figure_manifest.json` 图表是否齐全。
