# Thesis Gap Audit（论文就绪差距审计）

生成时间（UTC）：2026-02-27T14:03:18+00:00

## 1. 当前完成度快照
- 开题一致性审计：PASS=10 / PARTIAL=1 / FAIL=0  
  见 `reports/opening_alignment_audit.md`
- 任务交付审计：DONE=42 / TODO=0 / DONE缺失=0  
  见 `reports/task_audit.md`
- 对齐训练真实化：DPO/SimPO/KTO 全部 `simulation=false`  
  见 `reports/training/{dpo_real_metrics,simpo_metrics,kto_metrics}.json`

## 2. 距离“可支撑论文主结论”仍存在的差距
### Gap-G1（高优先级）
- 内容：完整规模 Layer-B（Qwen2.5-7B）主实验仍未产出真实主结果。
- 证据：`A10=PARTIAL`，仅有 blocker 报告。  
  见 `reports/small_real/qwen_layer_b_blocker.md`
- 影响：论文主结果表仍以 small-real/回退结果作为工程证据，主实验章说服力不足。

### Gap-G2（中优先级）
- 内容：LLM-as-a-Judge 已实现并可落盘，但当前未注入有效 key，Judge 结果为 skipped。
- 证据：`reports/judge/winrate/*_summary.json` 中 status=skipped（missing THIRD_PARTY_API_KEY）。
- 影响：WinRate 的 API Judge 口径尚未产出真实数值对比，只具备工程可运行性证据。

### Gap-G3（中优先级）
- 内容：真实对齐指标目前 DPO/SimPO/KTO 三者提升幅度接近，尚不足以形成“方法优劣”强结论。
- 证据：`reports/alignment_compare.md` 当前三者指标同量级。
- 影响：论文对齐方法章节需补更多控制变量实验（至少一组超参数或数据规模消融）。

## 3. 本轮已完成的“下一步”里程碑
- 已将 SimPO/KTO 从 proxy 升级为真实训练入口并接入 real-alignment 流程（带主模型超时回退）。
- 已刷新论文资产与审计，`A05` 从 PARTIAL 升级到 PASS。

新增/更新关键文件：
- `src/train/real_simpo_train.py`
- `src/train/real_kto_train.py`
- `scripts/train/run_real_alignment_pipeline.sh`
- `scripts/audit/build_thesis_ready_package.py`
- `scripts/audit/build_iteration_report.py`

## 4. 下一最小闭环（只剩一个关键阻塞）
1. 在具备 CUDA 的机器上运行：
   - `bash scripts/train/run_layer_b_qwen_autofallback.sh`
2. 产出并确认：
   - `reports/training/layer_b_qwen25_7b_sft_metrics.json`
   - 对应 loss/log/ckpt 可加载复现
3. 重新执行：
   - `python scripts/audit/check_opening_alignment.py`
   - `python scripts/audit/build_thesis_ready_package.py`
4. 验收目标：
   - `A10` 由 PARTIAL -> PASS，形成“开题一致性全 PASS”。

