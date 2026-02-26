# 开题一致性审计报告

- PASS: 8
- PARTIAL: 3
- FAIL: 0

| ID | 要求 | 状态 | 结论 | 关键证据 | 开题引用 |
|---|---|---|---|---|---|
| A01 | 仓库安全防护（数据/权重/密钥不得入库） | PASS | Repo Guard 与 .gitignore 关键规则存在。 | scripts/repo_guard.py<br>.gitignore | 【DOCX | 研究内容与难点 | 段落#1】 |
| A02 | 三层闭环（数据治理-检测-对齐）可执行 | PASS | 闭环入口齐全。 | scripts/data/run_data_governance_pipeline.py<br>scripts/train/run_small_real_pipeline.sh<br>scripts/train/run_real_alignment_pipeline.sh<br>scripts/eval/run_thesis_pipeline.sh<br>scripts/run_autonomous_iteration.sh | 【PDF | 页码p10 | 段落#1】<br>【DOCX | 题目与任务定义 | 段落#1】 |
| A03 | 真实数据构建与版本化可追溯 | PASS | real数据可用 train/dev/test=288/36/36。 | reports/real_dataset_summary.json<br>reports/real_dataset_report.md | 【PDF | 页码p12 | 段落#1】 |
| A04 | 真实训练证据链（loss/ckpt/eval/run-card） | PASS | small-real 与 real DPO 证据链齐全。 | reports/training/small_real_lora_v13_metrics.json<br>reports/small_real/small_real_lora_v13/loss_curve.csv<br>reports/small_real/small_real_lora_v13/loss_curve.png<br>reports/small_real/small_real_lora_v13/run_card.json<br>reports/training/dpo_real_metrics.json | 【PDF | 页码p11 | 段落#1】<br>【DOCX | 方法与实验设计 | 段落#1】 |
| A05 | 对齐方法覆盖（SFT + DPO/SimPO/KTO） | PARTIAL | DPO为真实训练；SimPO/KTO 当前为 proxy，方法覆盖完整但真实度部分不足。 | reports/training/dpo_real_metrics.json<br>reports/training/simpo_metrics.json<br>reports/training/kto_metrics.json<br>reports/alignment_compare.md | 【PDF | 页码p11 | 段落#1】<br>【DOCX | 方法与实验设计 | 段落#1】 |
| A06 | Baseline 覆盖（Med-PaLM/ChatDoctor/HuatuoGPT/DISC/Qwen） | PASS | baseline 覆盖完整。 | reports/thesis_assets/tables/baseline_audit_table.json | 【PDF | 页码p5 | 段落#1】<br>【PDF | 页码p12 | 段落#1】 |
| A07 | 评测指标覆盖（FactScore/WinRate/Rouge-L/Interception） | PASS | 指标覆盖满足开题口径。 | reports/eval_default.md<br>reports/thesis_assets/tables/main_results_real.csv | 【PDF | 页码p13 | 段落#1】<br>【DOCX | 方法与实验设计 | 段落#1】 |
| A08 | WinRate 与开题 GPT-4 Judge 口径一致性 | PARTIAL | 当前 WinRate 为离线规则口径，尚未落地 GPT-4 Judge 版本。 | eval/metrics.py<br>scripts/eval/run_sota_compare.py<br>reports/eval_default.md | 【PDF | 页码p13 | 段落#1】 |
| A09 | real/proxy 结果分层展示与口径隔离 | PASS | 双层表已形成。 | reports/thesis_assets/tables/main_results_dual_view.md<br>reports/thesis_assets/tables/baseline_audit_dual_view.md | 【PPT | 页码15 | 要点#7】 |
| A10 | 完整规模实验可行性与阻塞可审计 | PARTIAL | 当前环境无GPU，已输出 blocker，流程可继续但主实验结果待算力补齐。 | reports/small_real/qwen_layer_b_blocker.md<br>reports/training/layer_b_qwen25_7b_sft_metrics.json | 【PDF | 页码p13 | 段落#1】<br>【DOCX | 方法与实验设计 | 段落#1】 |
| A11 | 任务清单与交付物一致性 | PASS | 任务审计显示 DONE 项交付物完整。 | reports/task_audit.json<br>reports/task_audit.md | 【DOCX | 题目与任务定义 | 段落#1】 |
