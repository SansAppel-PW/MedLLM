# MedLLM 论文写作材料包（可直接用于初稿）

## 1. 使用方式
本文件把当前仓库产物映射到论文写作结构，目标是让你在 GPU 主实验完成后，快速落稿并保持“证据链可审计”。

建议写作顺序：
1. 先写第3章（方法与实验设计）
2. 再写第4章（系统实现）
3. 再写第5章（实验结果与消融）
4. 最后写第1/2章与摘要

## 2. 可主张与不可主张边界
### 2.1 当前可主张
- 已实现三层结构闭环：数据治理 -> 检测 -> 对齐【PDF | 页码p10 | 段落#1】。
- 已具备真实 small-real 与真实 DPO/SimPO/KTO 对齐证据链【PDF | 页码p11 | 段落#1】。
- 已构建可复现审计体系（Repo Guard、opening/task/gpu/interface audit）。

### 2.2 当前不可主张（GPU 主实验前）
- 不可声称 Qwen2.5-7B Layer-B 主实验已完成并优于全部基线。
- 不可将 proxy 背景表当成主结果表。

## 3. 章节-代码-证据映射
| 论文章节 | 可直接引用的工程证据 | 产物路径 |
|---|---|---|
| 第1章 研究背景与问题定义 | 开题结构化证据、目标与约束 | `docs/OPENING_PROPOSAL_EVIDENCE.md` |
| 第2章 相关工作 | baseline 审计表、复现可行性与局限 | `reports/thesis_assets/tables/baseline_audit_table.json` |
| 第3章 方法设计 | 三层体系、配置分层、训练/评测管线 | `src/` `configs/` `scripts/` |
| 第4章 系统实现 | 一键主线脚本、接口审计、运行门禁 | `scripts/train/run_gpu_thesis_mainline.sh` `scripts/audit/check_pipeline_interface_consistency.py` |
| 第5章 实验与结果 | 主结果表、消融表、误差案例、loss 曲线 | `reports/thesis_assets/tables/*.csv` `reports/small_real/*/loss_curve.png` `reports/error_analysis.md` |
| 第6章 总结与展望 | 风险、局限、后续工作 | `docs/PROJECT_STATUS_AUDIT.md` `reports/gpu_migration_readiness.md` |

## 4. 可直接落文的结果素材
### 4.1 主结果表
- `reports/thesis_assets/tables/main_results_real.csv`
- `reports/thesis_assets/tables/main_results_small_real.csv`
- `reports/thesis_assets/tables/main_results_dual_view.md`

### 4.2 baseline 与对比
- `reports/thesis_assets/tables/baseline_real_mainline.csv`
- `reports/thesis_assets/tables/baseline_proxy_background.csv`
- `reports/thesis_assets/tables/baseline_audit_dual_view.md`

### 4.3 消融
- `reports/thesis_assets/tables/ablation_small_real_runs.csv`
- `reports/thesis_assets/tables/dpo_beta_ablation.csv`
- `reports/dpo_beta_ablation.md`

### 4.4 训练与复现证据
- `reports/small_real/small_real_lora_v13/run_card.json`
- `reports/small_real/small_real_lora_v13/loss_curve.csv`
- `reports/small_real/small_real_lora_v13/loss_curve.png`
- `reports/training/dpo_real_metrics.json`
- `reports/training/simpo_metrics.json`
- `reports/training/kto_metrics.json`

### 4.5 评测与案例
- `reports/eval_default.md`
- `reports/detection_eval.md`
- `reports/error_analysis.md`
- `reports/thesis_assets/cases/error_cases_top30.jsonl`

## 5. 目前可用关键数值（写作前可直接核对）
- 开题一致性：PASS=10, PARTIAL=1, FAIL=0（`opening_alignment_audit.json`）。
- GPU 准备度：READY_FOR_GPU_MAINLINE=true（`gpu_migration_readiness.json`）。
- small-real LoRA（v13）：`train_loss=10.7346`，`final_eval_loss=10.7369`（small-real 闭环证据）。
- 真实偏好对齐（fallback 路径）：DPO/SimPO/KTO `pref_accuracy_after=0.25347`，`pair_count=288`。

说明：以上数值用于“当前阶段进展”描述。论文主结论必须以后续 GPU Layer-B 结果为主。

## 6. 论文正文模板（可改写）
### 6.1 方法章节模板（第3章）
“本研究构建了数据治理、幻觉检测与偏好对齐三层闭环框架。其中，数据层通过公开医疗数据集构建可追溯训练语料；检测层融合白盒不确定性与黑盒检索核查；对齐层在 SFT 基座上引入 DPO、SimPO、KTO 三类偏好优化策略，以评估不同对齐损失对医学问答可信性的影响。”

### 6.2 实现章节模板（第4章）
“工程实现采用脚本化一键流程，入口为 `run_gpu_thesis_mainline.sh`。流程内置 Repo Guard、接口一致性审计、数据自愈、训练自动回退和结果验收机制，确保每轮实验自动落盘 loss、checkpoint、eval 指标与 run card，并可通过审计脚本复核。”

### 6.3 结果章节模板（第5章）
“在 small-real 与 real-alignment 阶段，系统已完成真实训练闭环并生成可追溯产物。受限于当前本地算力，Layer-B Qwen2.5-7B 主实验尚未执行。迁移到 GPU 环境后，执行 `make gpu-mainline` 即可补齐主结果表并完成最终验收（A10=PASS）。”

### 6.4 局限与展望模板（第6章）
“当前阶段的主要限制在于完整规模主实验对 GPU 资源的依赖。后续工作将补齐 Layer-B 与 full-scale 训练，并在统一协议下扩展到更大参数规模模型，以进一步评估方法在复杂临床问答场景下的泛化能力与安全边界。”

## 7. 图表插入建议
- 图1：系统总体架构图（来源 `reports/thesis_assets/figures/pipeline_mermaid.md`，可在论文排版工具中渲染为矢量图）。
- 图2：small-real 训练 loss 曲线（`reports/small_real/small_real_lora_v13/loss_curve.png`）。
- 图3：误差案例类别统计（可基于 `error_cases_top30.jsonl` 二次作图）。
- 表1：主结果（`main_results_real.csv`）。
- 表2：baseline 可审计对比（`baseline_audit_dual_view.md`）。
- 表3：对齐消融（`dpo_beta_ablation.csv` + `ablation_small_real_runs.csv`）。

## 8. GPU 主实验后需要更新的段落
1. 第5章主结果：补入 Layer-B 行并更新排名与显著性讨论。
2. 第5章消融：将 fallback 结果与 Layer-B 结果区分讨论。
3. 摘要与结论：把“待补齐”措辞改为“已完成并通过审计”。

## 9. 最终答辩前检查清单
- `make gpu-mainline` 成功。
- `make gpu-closure` 全 PASS。
- `make opening-audit` 中 A10=PASS。
- `make thesis-ready` 产物齐全。
- 论文中所有表/图均可追溯到仓库路径与实验日志。

## 10. 参考引用锚点（开题材料）
- 三层框架与系统目标【PDF | 页码p10 | 段落#1】
- 对齐方法覆盖要求【PDF | 页码p11 | 段落#1】
- 指标体系与实验设计【PDF | 页码p13 | 段落#1】
- SFT + DPO/SimPO/KTO 实验口径【DOCX | 方法与实验设计 | 段落#1】
