# Stage2 资源感知迭代报告（2026-02-26）

## 1. 本轮目标
- 在模型口径锁定（Qwen2.5-7B/14B 或 Qwen3 小参数）前提下，保证训练受阻时项目不停止。
- 将工程推进到“扩容后可一键完成全部论文目标”的状态。

## 2. 已完成改造
1. 训练总流水线支持资源预检与自动跳过：
   - `scripts/train/run_real_alignment_pipeline.sh`
   - 输出：`reports/training/resource_preflight.json`、`reports/training/resource_skip_report.md`
2. 新增一键论文总控入口：
   - `scripts/pipeline/run_paper_ready.sh`
   - 覆盖：数据构建 -> 训练(可跳过) -> 评测 -> 验收
   - 输出状态总览：`reports/pipeline/paper_ready_status.md`
3. 评测脚本修复空数组参数问题，保证在 `set -u` 下稳定执行。
4. 对齐报告支持 skipped 状态，不再把“跳过训练”误报为真实训练结果。

## 3. 当前环境判定
- 资源探测结果：`mps`，无 CUDA 显存。
- 因此 Qwen2.5-7B/14B 真实训练默认触发跳过策略，项目继续推进其他模块。

## 4. 已验证命令
- 强制跳过训练并继续评测：
  `FORCE_SKIP_TRAINING=true DET_MAX=80 EVAL_MAX=80 SOTA_MAX=120 bash scripts/pipeline/run_paper_ready.sh`
- 强制跳过训练并执行端到端验收：
  `FORCE_SKIP_TRAINING=true RUN_EVAL=false RUN_E2E=true bash scripts/pipeline/run_paper_ready.sh`

## 5. 扩容后直接执行
- 7B真实训练 + 全链路：
  `MODEL_NAME=Qwen/Qwen2.5-7B-Instruct MODEL_TIER=7b ALIGNMENT_MODE=real FORCE_SKIP_TRAINING=false bash scripts/pipeline/run_paper_ready.sh`
- 14B真实训练 + 全链路：
  `MODEL_NAME=Qwen/Qwen2.5-14B-Instruct MODEL_TIER=14b ALIGNMENT_MODE=real FORCE_SKIP_TRAINING=false bash scripts/pipeline/run_paper_ready.sh`

## 6. 结论
- 已满足“训练受限不阻塞迭代”的工程要求。
- 当前仓库处于“可持续推进 + 可一键复跑 + 扩容即转真训”的论文就绪状态。
