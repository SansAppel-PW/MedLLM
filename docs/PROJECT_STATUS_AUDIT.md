# 项目现状审计与结构梳理（2026-02-27）

## 1. 审计结论
- 结论：当前仓库已达到“迁移到 GPU 环境后可一键执行主实验”的就绪状态，但尚未达到“本机即完美成功”。
- 依据：
  - `python scripts/audit/check_gpu_migration_readiness.py` 返回 `READY_FOR_GPU_MAINLINE`。
  - `python scripts/audit/verify_gpu_experiment_closure.py` 返回 `pass=3, fail=3`，失败项集中在 Layer-B Qwen2.5-7B 主实验缺口。
  - `python scripts/audit/check_opening_alignment.py` 返回 `pass=10, partial=1, fail=0`，唯一 `PARTIAL` 为 A10（完整规模实验受 GPU 资源限制）。
  - `python scripts/audit/check_pipeline_interface_consistency.py` 返回 `pass=6, fail=0`，一键主链接口调用一致。

## 2. 与开题要求的一致性
- 三层闭环（数据治理-检测-对齐）已具备可执行入口，满足主线框架要求【PDF | 页码p10 | 段落#1】。
- SFT + DPO/SimPO/KTO 方法覆盖已落地，符合方法设计要求【PDF | 页码p11 | 段落#1】【DOCX | 方法与实验设计 | 段落#1】。
- 指标体系与论文口径（FactScore/WinRate/Rouge-L/安全指标）已在评测与论文资产脚本中保留【PDF | 页码p13 | 段落#1】。

## 3. 剩余关键缺口（仅 GPU 侧）
1. 补齐 Layer-B Qwen2.5-7B 真实 SFT 训练并生成真实指标。
2. 通过 `gpu-closure --strict`，将 `A10` 从 `PARTIAL` 提升为 `PASS`。
3. 更新主结果表中的 Layer-B 行（`reports/thesis_assets/tables/main_results_real.csv`）。

## 4. 迁移后一键主线
```bash
python -m pip install -r requirements.txt
make gpu-mainline
make gpu-closure
make opening-audit
make thesis-ready
```

## 5. 当前代码结构（主干）
- `src/`: 数据、训练、评测、可视化核心实现
- `scripts/data`: 数据下载、构建、manifest 与统计
- `scripts/train`: small-real、layer-b、real alignment、GPU 主线入口
- `scripts/eval`: 评测、ablation、judge 与论文资产生成
- `scripts/audit`: 开题对齐审计、任务审计、GPU 就绪与闭环验收
- `configs/`: sanity / small / full 分层配置
- `docs/`: 运行手册、开题证据、合规与执行清单

## 6. 清理策略
- 保留：论文主线必须文件（训练/评测/审计/迁移脚本与核心报告模板）。
- 归档：早期阶段性过程文档（Step1/Step2/Step4），避免与当前状态混淆。
- 约束：不删除可追溯证据链文件；仅清理重复或历史过时叙述。
