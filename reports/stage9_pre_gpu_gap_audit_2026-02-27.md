# Stage9 Pre-GPU Gap Audit (2026-02-27)

## 1. 当前状态快照
- 分支：`codex/worktree`
- 基础迁移自检：`reports/migration/handoff_readiness.json` -> `ready=true`
- 论文就绪度：`reports/thesis_support/thesis_readiness.json` -> `PASS=5, DEFERRED=2, FAIL=0`
- GPU 严格完成性：`reports/migration/gpu_completion_check.json` -> `strict_pass=false`
- v2 融合回退归因：`reports/detection_eval_v2_hybrid_llm_impact.md`（当前全量样本 `1200`，`llm_used=80`）

## 2. 已在本地补齐的关键能力（无需 GPU）
1. 新增 GPU 后严格完工校验脚本：`scripts/migration/check_gpu_completion.py`
2. 将严格校验接入一键 GPU 流水线：`scripts/migration/run_gpu_thesis_experiment.sh`
3. 强化论文就绪审计：`scripts/audit/check_thesis_readiness.py`
   - 训练不再仅检查 SFT 文件存在
   - 必须检查 SFT/DPO/SimPO/KTO 的 real/skipped 状态
   - 真实 SFT loss 曲线改为严格校验
4. 新增 v2 规则+LLM 回退效果归因脚本：`scripts/eval/analyze_llm_fallback_impact.py`
5. 将归因结果接入鲁棒评测脚本：`scripts/eval/run_detection_robustness.sh`
6. 文档与入口更新：`README.md`、`docs/GPU_MIGRATION_RUNBOOK.md`、`Makefile`

## 3. 当前距离“论文级真实实验完成”的剩余差距
1. **R2（DEFERRED）**：SFT/DPO/SimPO/KTO 仍为 `skipped`，缺真实训练产物（real metrics + final checkpoint）。
2. **R4（DEFERRED）**：缺真实 Qwen2.5-7B Layer-B SFT loss 曲线（目前仅 tiny/proxy 曲线）。

## 4. GPU 迁移后一键闭环路径（无需改代码）
```bash
make gpu-bootstrap
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" MODEL_TIER="7b" ALLOW_SKIP_TRAINING=false FORCE_SKIP_TRAINING=false make gpu-run
make gpu-complete-check
```

## 5. 完成判定（进入论文写作“真实实验已闭环”状态）
需同时满足：
- `reports/migration/gpu_completion_check.json` 中 `strict_pass=true`
- `reports/thesis_support/thesis_readiness.json` 中 `FAIL=0` 且 `DEFERRED=0`
- 真实训练曲线存在于 `reports/thesis_assets/figures/`（Qwen2.5-7B Layer-B）
