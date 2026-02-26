# 资源感知执行说明

本文档约束训练流水线在算力不足时的行为，目标是“不中断项目推进”。

## 1. 模型口径
- 当前训练口径锁定：
  - `Qwen2.5-7B/14B`
  - 或 `Qwen3` 小参数模型

## 2. 自动探测与跳过
入口：`scripts/train/run_real_alignment_pipeline.sh`

执行时会产出：
- `reports/training/resource_preflight.json`：硬件探测结果
- `reports/training/resource_skip_report.md`：训练跳过原因（若触发）

默认策略：
- 先尝试真实训练（`ALIGNMENT_MODE=real`）。
- 若不满足资源门槛或训练失败且 `ALLOW_SKIP_TRAINING=true`，自动写入 `skipped` 指标并继续流程。
- `save_total_limit` 固定为 `2`，避免磁盘膨胀。

## 3. 常用参数
- `MODEL_NAME`：目标模型，如 `Qwen/Qwen2.5-7B-Instruct`
- `MODEL_TIER`：`auto|small|7b|14b`
- `ALIGNMENT_MODE`：`real|proxy`
- `ALLOW_SKIP_TRAINING`：默认 `true`
- `FORCE_SKIP_TRAINING`：默认 `false`
- `MIN_CUDA_MEM_GB_7B`：默认 `18`
- `MIN_CUDA_MEM_GB_14B`：默认 `36`

## 4. 一键执行
推荐：
```bash
make paper-ready
```

状态总览：
- `reports/pipeline/paper_ready_status.md`
