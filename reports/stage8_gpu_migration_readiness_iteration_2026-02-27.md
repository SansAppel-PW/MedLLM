# Stage 8：GPU 迁移即跑准备迭代（2026-02-27）

## 目标
- 在当前无 CUDA 训练环境下，把剩余差距转化为“迁移后无需改代码、直接开跑”的可执行交接系统。

## 新增模块
1. `scripts/migration/bootstrap_gpu_env.sh`
- 远端环境安装脚本（venv/system 可选）。
- 自动输出 CUDA 探测结果并给出告警。

2. `scripts/migration/run_gpu_thesis_experiment.sh`
- GPU 环境一键执行真实训练 + 评测 + 完备度审计。
- 默认 `ALLOW_SKIP_TRAINING=false`，避免伪“真实训练”结果。
- 新增 `DRY_RUN=true` 方便本地验证流程。

3. `scripts/migration/build_gpu_handoff_manifest.py`
- 自动生成迁移交接清单（commit、关键文件 hash、执行命令）。
- 输出：
  - `reports/migration/gpu_handoff_manifest.json`
  - `reports/migration/gpu_handoff_manifest.md`

4. `scripts/migration/check_handoff_readiness.py`
- 自动检查迁移必要文件完整性。
- 输出：
  - `reports/migration/handoff_readiness.md`
  - `reports/migration/handoff_readiness.json`

## 工程接入
- `Makefile` 新增目标：
  - `make gpu-manifest`
  - `make gpu-check`
  - `make gpu-bootstrap`
  - `make gpu-run`
- `README.md` 增加 GPU 迁移章节。
- 新文档：`docs/GPU_MIGRATION_RUNBOOK.md`。

## 当前可验证结果
- 交接清单已生成：`reports/migration/gpu_handoff_manifest.*`
- 交接自检结果：`ready=true, missing_count=0`
- `run_gpu_thesis_experiment.sh` 本地 dry-run 已通过。

## 结论
- 当前环境可完成的准备工作已覆盖：
  - 训练评测代码、偏差审计、LLM 回退增强、迁移即跑编排、交接校验。
- 剩余唯一实质差距已被严格限定为“GPU 上的真实训练执行”。
