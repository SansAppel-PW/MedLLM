# AutoDL 部署方案与保姆级指南（MedLLM）

## 1. 先说结论：租什么显卡最合适

基于当前项目训练脚本门槛（`MIN_CUDA_MEM_GB_7B=18`、`MIN_CUDA_MEM_GB_14B=36`）与工程稳定性，推荐如下：

1. 只跑 Qwen2.5-7B（论文主线首选性价比）：`RTX 4090/4090D 24GB`
2. 跑 7B 并希望更稳、OOM 更少：`A100 40GB` 或 `L20 48GB`
3. 要尝试 Qwen2.5-14B：优先 `A100/A800/H20 80GB+`（40GB虽可能勉强跑，但风险高）

建议你在 AutoDL 首轮直接选：
- `A100 40GB`（平衡稳定性和成本，7B最稳）
- 预算紧张时退而求其次 `4090 24GB`

若你已经租了 `V100-32GB * 2`：
- 先跑 `Qwen2.5-7B` 完全可行（建议优先完成这一轮论文主链）。
- 当前项目已内置“预 Ampere 自动精度降级”：检测到 V100 会自动 `bf16=false`、`fp16=true`，无需你手动改参数。
- 可直接使用双卡模板：`configs/runtime/v100_dual_32g.env` + `bash scripts/migration/run_day1_v100_dual.sh`。

## 2. 选型依据

- 项目脚本对资源有明确门槛，低于门槛会自动跳过训练并写入证据（不是失败，但无法达到 strict 完工）。
- 当前 strict 完工检查要求真实训练产物（非 skipped）+ checkpoint + loss 曲线。
- AutoDL 官方文档说明了 GPU 选型、CPU/内存随 GPU 线性分配、以及 4090/A100/A800/L20/H20 等需 CUDA 11.1+。

参考：
- AutoDL GPU 选型文档：https://www.autodl.com/docs/gpu/

## 3. AutoDL 实例建议配置

## 3.1 基础配置
- GPU：按第 1 节选型
- 系统盘：建议 `>= 100GB`
- 数据盘：建议 `>= 200GB`（模型缓存 + 中间产物 + checkpoint）
- 镜像：官方 PyTorch + CUDA 11.8/12.x 镜像
- Python：3.10/3.11

## 3.2 环境变量建议
为避免系统盘爆满，建议设置缓存目录到数据盘：

```bash
export HF_HOME=/root/autodl-tmp/hf
export HUGGINGFACE_HUB_CACHE=/root/autodl-tmp/hf/hub
export TRANSFORMERS_CACHE=/root/autodl-tmp/hf/transformers
mkdir -p "$HF_HOME" "$HUGGINGFACE_HUB_CACHE" "$TRANSFORMERS_CACHE"
```

## 4. Day1 零思考执行（推荐）

项目已内置一键脚本：`day1_run.sh`

## 4.1 一条命令跑完整流程

```bash
bash day1_run.sh
```

脚本会自动执行：
1. 同步分支代码
2. 检查 `.env` / API Key
3. `nvidia-smi`、CUDA 可用性校验
4. `make gpu-bootstrap`
5. `make gpu-check` + GPU dry-run
6. 真正执行 `make gpu-run`
7. 执行 `make gpu-complete-check`
8. 生成 day1 总结

## 4.2 常用参数（建议复制）

```bash
BRANCH=codex/worktree \
MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" \
MODEL_TIER="7b" \
ALLOW_SKIP_TRAINING=false \
FORCE_SKIP_TRAINING=false \
ENABLE_LLM_JUDGE=false \
ENABLE_LLM_RISK_JUDGE=true \
ENABLE_V2_LLM_FALLBACK=true \
bash day1_run.sh
```

## 4.3 V100 双卡模板启动（推荐）

```bash
bash scripts/migration/run_day1_v100_dual.sh
# 或
make day1-v100-dual
```

该入口会自动加载 `configs/runtime/v100_dual_32g.env`，并沿用 `day1_run.sh` 全流程。
参数细节见：`docs/V100_DUAL_CARD_TEMPLATE.md`。

只做流程探测不真正跑训练：

```bash
DAY1_DRY_RUN=true bash day1_run.sh
```

## 5. 手动流程（不用 day1 脚本时）

```bash
git clone <你的仓库URL> MedLLM_codex
cd MedLLM_codex
git checkout codex/worktree
git pull --ff-only

cat > .env <<'ENV'
OPENAI_BASE_URL=https://api.gptsapi.net/v1
OPENAI_API_KEY=你的key
ENV
chmod 600 .env

make gpu-bootstrap
make gpu-check
DRY_RUN=true bash scripts/migration/run_gpu_thesis_experiment.sh

MODEL_NAME="Qwen/Qwen2.5-7B-Instruct" MODEL_TIER="7b" ALLOW_SKIP_TRAINING=false FORCE_SKIP_TRAINING=false make gpu-run
make gpu-complete-check
```

## 6. 成功判定标准（论文级）

同时满足以下三条才算“真正跑完”：
1. `reports/migration/gpu_completion_check.json` 中 `strict_pass=true`
2. `reports/thesis_support/thesis_readiness.json` 中 `ready_for_writing=true`
3. 训练指标文件中 `skipped=false` 且 final checkpoint 存在

## 7. 输出文件你该看什么

## 7.1 首看
- `reports/migration/day1_run_summary.md`
- `reports/migration/gpu_completion_check.md`
- `reports/thesis_support/thesis_readiness.md`

## 7.2 核心训练产物
- `reports/training/layer_b_qwen25_7b_sft_metrics.json`
- `reports/training/dpo_metrics.json`
- `reports/training/simpo_metrics.json`
- `reports/training/kto_metrics.json`
- `checkpoints/layer_b/qwen25_7b_sft/final`
- `checkpoints/dpo-real-baseline/final`
- `checkpoints/simpo-real-baseline/final`
- `checkpoints/kto-real-baseline/final`

## 7.3 论文产物
- `reports/eval_default.md`
- `reports/sota_compare.md`
- `reports/error_analysis.md`
- `reports/thesis_support/thesis_draft_material.md`
- `reports/thesis_support/experiment_record.json`

## 8. 常见坑与处理（按优先级）

## 8.1 strict_pass=false
优先看：`reports/migration/gpu_completion_check.md`

常见原因：
- 训练仍是 skipped（显存不足/未启用 CUDA）
- checkpoint final 目录缺失
- 真实 SFT 曲线未产出

## 8.2 CUDA 可见但仍跳过训练
- 检查是否误设 `FORCE_SKIP_TRAINING=true`
- 检查 `MODEL_TIER` 与显存是否匹配（14B 不建议 40GB 以下）
- 若是 V100：确认日志中出现自动精度提示（pre-Ampere -> fp16）；若没有，更新到最新分支代码后重跑。

## 8.3 OOM
- 脚本已内置自动降级重试（batch 降低、grad acc 提升）
- 若仍 OOM，升级显卡规格（4090 -> A100 40GB -> A100/A800/H20 80GB）

## 8.4 API 评测失败
- 检查 `.env` 和 key
- 临时关闭：
  - `ENABLE_LLM_JUDGE=false`
  - `ENABLE_LLM_RISK_JUDGE=false`
  - `ENABLE_V2_LLM_FALLBACK=false`

## 8.5 系统盘满
- 把 HF/transformers cache 指到数据盘（见 3.2）

## 9. 预算与时长建议

1. 首次严谨跑通（建议）：A100 40GB，先跑 7B 完整闭环
2. 若需 14B：直接 80GB 级别卡，减少反复失败时间成本
3. 时间优先于小额省钱：优先“更稳显卡”，避免多次重试导致总花费更高

## 10. 推荐执行顺序（实战）

1. 先用 `DAY1_DRY_RUN=true` 验证流程
2. 再真跑 7B（A100 40GB / 4090）
3. strict_pass 通过后再考虑 14B 扩展实验
4. 完成后导出 `reports/` 与 `checkpoints/*/final` 做备份
