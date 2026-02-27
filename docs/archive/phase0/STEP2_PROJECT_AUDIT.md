# Step 2 项目现状审计报告

## 0. 审计范围与方法
- 分支：`codex/worktree-gpt-prompt`
- 审计对象：`src/`、`scripts/`、`configs/`、`data/`、`reports/`、`docs/`
- 审计命令：`find`、`rg`、`git ls-files`、`du`、`python scripts/audit/check_task_completion.py`

## 1. 现状结论（摘要）
- 工程骨架较完整：已有数据构建、检测、训练、评测、报告脚本。
- 论文级风险仍存在：真实对齐训练（DPO/SimPO/KTO）未落地，当前主流程仍含 proxy 语义。
- 可复现基础已部分具备：`real_sft_train.py` 会落盘 manifest 与 metrics，但尚未统一形成“一键全链路”强约束入口。
- 仓库安全风险存在：此前缺少 staging 级 Repo Safety Guard，且仓库已跟踪 `data/` 下轻量样本文件，存在后续误提交大文件风险。

## 2. 结构完整性审计
- 已存在的核心子系统：
  - 数据：`scripts/data/build_real_dataset.py`、`run_data_governance_pipeline.py`
  - 训练：`src/train/real_sft_train.py` + `scripts/train/run_layer_b_real_sft.sh`
  - 评测：`scripts/eval/run_thesis_pipeline.sh`、`eval/run_eval.py`
  - 报告：`scripts/eval/build_thesis_assets.py`
- 缺失或未闭环项：
  - 真实 DPO/SimPO/KTO 训练器未上线，`run_real_alignment_pipeline.sh` 的 `ALIGNMENT_MODE=real` 仍不可用。
  - Repo 级防误传机制缺失（本轮 Step 3 修复）。
  - 环境基线未自动固化（`pip freeze`/`conda env export` 未强制纳入 run card）。

## 3. 可复现性缺陷审计
- 依赖侧：当前系统 Python 缺少 `torch/transformers/peft/trl/pytest`，直接影响真实训练与测试执行。
- 训练侧：SFT 已有真实入口，但对齐阶段仍是“真实 SFT + 代理对齐”的混合态。
- 测试侧：当前回归测试依赖 `pytest`，在默认环境不可直接执行。
- 一键闭环侧：`Makefile` 仅提供 setup/check-env/run-config，尚无统一 `prepare->train->eval->report` 入口命令。

## 4. 冗余与口径风险
- 历史报告中存在“proxy/simulation”与“real”并存，若论文撰写未区分，会造成证据链口径混淆。
- `reports/` 存在阶段性报告，需在后续论文引用时明确“真实实验结果”与“流程验证结果”的物理隔离与文档隔离。

## 5. 数据/权重入库风险点
- 当前已跟踪 `data/` 下若干轻量样本（json/jsonl），说明仓库历史策略允许“数据文件进入版本库”。
- 当前未见已跟踪大权重后缀（`.pt/.safetensors/.ckpt/.gguf`）与超大文件（>10MB）。
- 当前最大已跟踪文件是 `开题报告-胡佩文.pptx`（约 6.6MB），未超 10MB 阈值。

## 6. 审计结论
- 可以直接推进下一阶段，但必须先完成：
  1. Repo Safety Guard + `.gitignore` 强制策略；
  2. `.env.example` 与密钥注入规范；
  3. 三层实验目录与产物隔离的执行约束；
  4. 小规模真实训练闭环（真实 forward/backward、loss、ckpt、eval、图表、run card）。
