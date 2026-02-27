# V100 双卡专用参数模板（2xV100-32GB）

本文档给出项目在 `V100-32GB x2` 上的默认参数模板与执行方式，目标是以最小改动稳定完成 Qwen2.5-7B 论文主链实验。

## 1. 模板文件

- 参数模板：`configs/runtime/v100_dual_32g.env`
- 一键入口：`scripts/migration/run_day1_v100_dual.sh`

## 2. 一键执行（推荐）

```bash
cd /path/to/MedLLM_codex

# 1) 准备 API 凭证（若已存在 .env 可跳过）
cat > .env <<'ENV'
OPENAI_BASE_URL=https://api.gptsapi.net/v1
OPENAI_API_KEY=YOUR_KEY
ENV
chmod 600 .env

# 2) 使用 V100 双卡模板直接启动 Day1 全流程
bash scripts/migration/run_day1_v100_dual.sh
```

## 3. 手动执行（可控）

```bash
cd /path/to/MedLLM_codex
set -a
source configs/runtime/v100_dual_32g.env
set +a

make gpu-bootstrap
make gpu-check
DRY_RUN=true bash scripts/migration/run_gpu_thesis_experiment.sh
make gpu-run
make gpu-complete-check
```

## 4. 模板关键参数说明

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `CUDA_VISIBLE_DEVICES` | `0,1` | 固定双卡可见，供 `device_map=auto` 调度。 |
| `BF16` / `ALIGN_BF16` | `false` | V100 为 pre-Ampere，不使用 bf16。 |
| `FP16` / `ALIGN_FP16` | `true` | 强制 fp16，兼容 V100。 |
| `LOAD_IN_4BIT` / `ALIGN_LOAD_IN_4BIT` | `true` | 启用 QLoRA 4bit，降低显存占用。 |
| `TRAIN_BSZ` / `ALIGN_TRAIN_BSZ` | `1` | 单卡微批固定 1，减少 OOM 风险。 |
| `GRAD_ACC` / `ALIGN_GRAD_ACC` | `24` / `32` | 通过梯度累积维持有效 batch。 |
| `MIN_CUDA_MEM_GB_7B` | `30` | 7B 训练准入阈值。 |
| `MIN_CUDA_MEM_GB_14B` | `72` | 14B 阈值设高，避免在双 V100 上误触发。 |

## 5. OOM 时的快速降级顺序

按顺序调整并重跑：

1. `MAX_LENGTH=1024`
2. `GRAD_ACC=32` 且 `ALIGN_GRAD_ACC=48`
3. `ALIGN_MAX_STEPS=180`
4. 关闭高成本评测：`ENABLE_LLM_RISK_JUDGE=false ENABLE_V2_LLM_FALLBACK=false`

示例：

```bash
MAX_LENGTH=1024 \
GRAD_ACC=32 \
ALIGN_GRAD_ACC=48 \
ALIGN_MAX_STEPS=180 \
ENABLE_LLM_RISK_JUDGE=false \
ENABLE_V2_LLM_FALLBACK=false \
bash scripts/migration/run_day1_v100_dual.sh
```

## 6. 验收标准

完成后需检查：

1. `reports/migration/gpu_completion_check.json` 中 `strict_pass=true`
2. `reports/thesis_support/thesis_readiness.json` 中 `ready_for_writing=true`
3. `reports/training/layer_b_qwen25_7b_sft_metrics.json` 中 `skipped=false`

## 7. 可选切换到 Qwen3-8B

若要对照实验切换模型：

```bash
MODEL_NAME="Qwen/Qwen3-8B" MODEL_TIER="7b" bash scripts/migration/run_day1_v100_dual.sh
```

若显存压力明显增加，优先降低 `MAX_LENGTH` 与提升 `GRAD_ACC`。
