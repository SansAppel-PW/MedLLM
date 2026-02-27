# MedLLM 完整使用说明（CPU 预演 + GPU 一键主实验）

## 1. 文档目标
本说明用于确保你把项目迁移到 GPU 租赁环境后，能够直接完成论文主线实验闭环，并输出可写入论文的全部证据链资产。

适用范围：
- 本地无 GPU 环境：做代码审计、流程预演、small-real 闭环与文档资产准备。
- GPU 环境：执行 Layer-B 主实验 + 对齐 + 评测 + 论文资产打包。

## 2. 当前项目状态（2026-02-27）
- 开题对齐审计：`PASS=10, PARTIAL=1, FAIL=0`。
- 任务完成审计：`DONE=42/42`。
- GPU 迁移就绪：`READY_FOR_GPU_MAINLINE=true`。
- GPU 闭环审计：`PASS=3, FAIL=3`（失败项均与 Layer-B GPU 主实验缺口相关）。

结论：当前仓库属于“迁移后可一键主实验”的状态，不是“本机已经完成最终主实验”的状态。

## 3. 目录与职责
- `src/`: 训练、评测、数据、检测核心实现。
- `scripts/data/`: 数据下载、构建、manifest、统计。
- `scripts/train/`: small-real、Layer-B、alignment、GPU 主线脚本。
- `scripts/eval/`: 综合评测、误差分析、论文资产导出。
- `scripts/audit/`: 开题一致性、任务闭环、GPU readiness/closure、接口一致性。
- `configs/`: 分层配置（sanity/small/full）。
- `reports/`: 指标、图表、run card、论文资产。
- `docs/`: 手册、开题证据、执行清单、审计报告。

## 4. 环境准备
### 4.1 基础依赖
```bash
make setup
make check-env
```

### 4.2 密钥（仅当启用 LLM Judge）
```bash
cp .env.example .env
# 填写 THIRD_PARTY_API_KEY
# THIRD_PARTY_BASE_URL 默认 https://api.gptsapi.net/v1
```

## 5. 本地（无 GPU）推荐执行顺序
### 5.1 基础审计
```bash
make repo-guard
make interface-audit
make opening-audit
make task-audit
make gpu-readiness
```

### 5.2 small-real 闭环（可在 CPU/MPS 预演）
```bash
make ensure-real-data
make small-real
make real-alignment
make thesis-ready
```

### 5.3 产物检查
关键产物路径：
- `reports/small_real/<run_tag>/run_card.json`
- `reports/small_real/<run_tag>/loss_curve.{csv,png,pdf}`
- `reports/training/dpo_real_metrics.json`
- `reports/training/simpo_metrics.json`
- `reports/training/kto_metrics.json`
- `reports/thesis_assets/tables/main_results_real.csv`

## 6. GPU 环境一键主实验
### 6.1 迁移前本机确认
```bash
make gpu-readiness
make gpu-mainline-dryrun
```

### 6.2 GPU 主实验一键执行
```bash
python -m pip install -r requirements.txt
make gpu-mainline
```

`make gpu-mainline` 内部顺序：
1. Repo Guard
2. 接口一致性审计
3. 数据资产自愈（bootstrap + ensure-real-data）
4. Layer-B Qwen2.5-7B 自动回退训练
5. 真实对齐（DPO/SimPO/KTO）
6. 综合评测（可选 LLM Judge）
7. thesis-ready 打包
8. 开题/任务/GPU-closure 审计

### 6.3 GPU 验收
```bash
make gpu-closure
make opening-audit
make thesis-ready
```

通过标准：
- `reports/gpu_experiment_closure.md` 全部 PASS
- `reports/opening_alignment_audit.md` 中 A10=PASS
- `reports/thesis_assets/tables/main_results_real.csv` 含 Layer-B 主结果行

## 7. 常用环境变量
### 7.1 主线训练
- `PYTHON_BIN`：统一 Python 解释器路径（建议 `.venv/bin/python`）
- `REQUIRE_GPU`：`run_gpu_thesis_mainline.sh` 是否强制检查 GPU，默认 `1`
- `DPO_MAX_STEPS/DPO_MAX_LENGTH/DPO_EPOCHS`：真实 DPO 控制参数
- `SIMPO_PRIMARY_TIMEOUT/KTO_PRIMARY_TIMEOUT`：主模型超时回退阈值

### 7.2 评测
- `ENABLE_LLM_JUDGE`：是否启用外部 Judge，默认 `0`
- `JUDGE_MODEL`：Judge 模型名，默认 `gpt-4o-mini`
- `KB_SOURCE_SPLITS`：构建 KB 的 split，默认 `train`
- `EVAL_SPLITS`：评测 split，默认 `validation,test`

## 8. 质量门禁（建议固定执行）
```bash
make repo-guard
make interface-audit
make opening-audit
make task-audit
pytest -q tests
```

## 9. 常见问题与处理
### 9.1 无 GPU
现象：Layer-B 不执行，生成 blocker 报告。
处理：迁移到 CUDA 主机后执行 `make gpu-mainline`。

### 9.2 OOM
现象：Qwen7B 训练中断。
处理：脚本已内置 3 档自动降级（2048/16 -> 1536/32 -> 1024/64），无需手工改参。

### 9.3 Judge 失败
现象：WinRate Judge 报错。
处理：检查 `.env` 密钥与网络，必要时 `ENABLE_LLM_JUDGE=0` 跳过并先完成主线。

### 9.4 依赖解释器不一致
现象：脚本在不同 Python 环境下行为不一致。
处理：统一 `PYTHON_BIN=.venv/bin/python`，并执行 `make interface-audit` 验证接口一致性。

## 10. 复现与审计清单
每轮实验必须保留：
- config 快照
- 数据 manifest
- run card（含 commit hash）
- loss 原始数据与图
- checkpoint manifest
- eval 指标 JSON/CSV

建议在每次里程碑后执行：
```bash
make repo-guard
git add -A
git commit -m "milestone: <具体内容>"
git push
```
