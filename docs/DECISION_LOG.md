# Decision Log

## 2026-02-26 | D001 | Small Real 闭环先于 Qwen7B
- 背景：开题目标要求三层闭环与真实训练证据链，但当前执行环境无 CUDA，且网络访问模型仓库不稳定。  
  `【DOCX | 三、课题技术路线及研究方案 | 段落#T03R001】` `【PDF | 页码p13 | 段落/条目#PG013L001】`
- 决策：先完成 Small Real 真实训练闭环（离线缓存小模型 + LoRA），并把 Qwen7B/14B 迁移为下一阶段目标。
- 理由：
  1. 保证真实 forward/backward、loss、checkpoint、eval、run card 证据链先落地；
  2. 避免在算力受限场景下阻塞整个论文工程推进；
  3. 保持与开题“三层实验结构”一致：先 Small Real，再 Full。  
     `【PDF | 页码p10 | 段落/条目#PG010L001】`
- 产物：
  - `scripts/train/run_small_real_pipeline.sh`
  - `reports/small_real/`（指标、图表、run card、结论）
  - `reports/training/small_real_lora_v3_metrics.json`

## 2026-02-26 | D002 | 训练脚本兼容 transformers 4.x/5.x
- 背景：环境安装到 transformers 5.2 后，`TrainingArguments` 和 `Trainer` 参数发生不兼容。
- 决策：在 `src/train/real_sft_train.py` 中加入动态签名兼容与 CPU 自愈降级（禁 4bit、8bit optim fallback、bf16/fp16 fallback）。
- 理由：
  1. 保持脚本跨环境可运行；
  2. 让失败路径自动降级，而不是中断流程；
  3. 对论文复现实验更稳健。
- 产物：
  - `src/train/real_sft_train.py`（兼容逻辑 + 环境快照写入 manifest）
