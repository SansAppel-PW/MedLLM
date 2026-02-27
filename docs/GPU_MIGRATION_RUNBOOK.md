# GPU Migration Runbook

本手册用于将当前项目迁移到租赁 GPU 环境后，做到“拉代码即开跑真实实验”。

## 1. 迁移前（本地）
在当前仓库生成交接清单：

```bash
python3 scripts/migration/build_gpu_handoff_manifest.py \
  --model-name Qwen/Qwen2.5-7B-Instruct \
  --model-tier 7b
```

输出：
- `reports/migration/gpu_handoff_manifest.json`
- `reports/migration/gpu_handoff_manifest.md`

## 2. GPU 机器环境准备
拉代码后，在项目根目录执行：

```bash
bash scripts/migration/bootstrap_gpu_env.sh
```

可选参数：
- `PYTHON_BIN`：默认 `python3`
- `INSTALL_METHOD`：`venv`（默认）或 `system`
- `PIP_EXTRA_INDEX_URL`：例如 `https://download.pytorch.org/whl/cu121`

## 3. 一键真实实验（推荐）
执行真实训练 + 全评测 + 论文材料：

```bash
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" \
MODEL_TIER="7b" \
ALLOW_SKIP_TRAINING=false \
FORCE_SKIP_TRAINING=false \
bash scripts/migration/run_gpu_thesis_experiment.sh
```

默认行为：
- 要求检测到 CUDA（未检测到会直接退出，防止伪“真实训练”）
- 若启用 API 评测（LLM Judge / 风险判别 / LLM 回退），会检查 `.env` 或 `OPENAI_API_KEY` 是否存在
- `ALIGNMENT_MODE=real`
- 启用 v2 偏差审计
- 默认执行严格完成性校验（`scripts/migration/check_gpu_completion.py`，要求真实训练非 skipped）
- 可选启用：
  - `ENABLE_LLM_RISK_JUDGE=true`
  - `ENABLE_V2_LLM_FALLBACK=true`
  - `ALLOW_DEFERRED_READINESS=true`（仅在需要临时放宽门槛时）

## 4. 关键验收文件
- 训练：`reports/training/*.json`
- 检测：`reports/detection_eval*.md`
- 融合回退归因：`reports/detection_eval_v2_hybrid_llm_impact.md`（启用 LLM 回退时）
- 对比：`reports/sota_compare.md`
- 论文材料：`reports/thesis_support/thesis_draft_material.md`
- 完备度：`reports/thesis_support/thesis_readiness.md`
- GPU 运行状态：`reports/migration/gpu_run_status.md`
- 严格完成性：`reports/migration/gpu_completion_check.md`

## 5. 常见问题
1. CUDA 可见但训练仍被跳过：
   - 检查 `MIN_CUDA_MEM_GB_7B` / `MIN_CUDA_MEM_GB_14B` 是否过高。
2. OOM：
   - 训练脚本内置自动降级（减小 batch，增大 gradient accumulation，启用 gradient checkpointing）。
3. API 评测失败：
   - 检查 `.env` 中 `OPENAI_BASE_URL` 与 `OPENAI_API_KEY`。
