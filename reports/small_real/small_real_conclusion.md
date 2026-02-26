# Small Real 真实闭环结论（阶段性）

## 1) 实验目标与口径
- 本轮目标是完成“小规模真实训练层”的端到端证据链（真实 forward/backward、loss、checkpoint、eval、run card、图表）。  
  `【DOCX | 三、课题技术路线及研究方案 | 段落#T03R001】` `【PDF | 页码p10 | 段落/条目#PG010L001】`
- 由于当前运行环境无 CUDA 且网络对模型仓库访问不稳定，本轮使用离线缓存的小模型完成闭环，Qwen 7B/14B 作为下一阶段迁移目标。  
  `【PDF | 页码p12 | 段落/条目#PG012L001】` `【PPT | 页码#15 | 要点#S015H005】`

## 2) 关键结果摘要
- 训练（真实）：`reports/training/small_real_tiny_gpt2_lora_v2_metrics.json`
  - `train_loss=10.7347`
  - `final_eval_loss=10.7369`
- 评测：`reports/small_real/eval_metrics.json`
  - `exact_match=0.0`
  - `rouge_l_f1=0.0`
  - `char_f1=0.0`
- 证据链：
  - run manifest: `checkpoints/small_real/tiny_gpt2_lora_v2/run_manifest.json`
  - train log: `logs/small_real/tiny_gpt2_lora_v2/train_log.jsonl`
  - loss 曲线: `reports/small_real/loss_curve.{csv,png,pdf}`
  - run card: `reports/small_real/run_card.{json,md}`
  - baseline 对比表（Base vs LoRA）：`reports/small_real/small_real_lora_v3/baseline_compare.{csv,md}`

## 3) 结论与解释
- 系统层面：本轮已证明小规模真实训练闭环可执行，且可在离线模式下复现实验工件。
- 指标层面：当前数据规模仅 1 train + 1 dev，且 `Base vs LoRA` 对照指标一致（均为 0），说明此轮不具统计意义，仅可作为“工程闭环验证”证据。
- 论文层面：本轮结果应归入“Small Real 训练可行性验证”，不得作为主实验结论。

## 4) 局限性与下一步
- 局限性：
  - 非 Qwen 主模型，且样本规模极小；
  - 尚未覆盖 DPO/SimPO/KTO 真实对齐训练；
  - baseline 对比表仍需补齐。
- 下一步（最小闭环）：
  1. 迁移到 Qwen2.5-7B 或 Qwen3 小模型（优先 GPU 环境）；
  2. 扩展样本规模并生成可解释误差分析；
  3. 补齐 baseline 对比表与至少 1 组消融。  
  `【DOCX | 四、工作进度安排 | 段落#T04R001】` `【PDF | 页码p13 | 段落/条目#PG013L001】`
