# 渐进式开发 Roadmap（2026-02-26）

## M1（已完成）安全与约束收敛
- 加固 `.gitignore`（模型权重/检查点/数据集/.env）。
- 本地 `.env` 注入完成，避免硬编码 key。
- 开题三份材料完成结构化审计与疑点收敛。

## M2（已完成）评测链路补齐
- 新增 `eval/llm_judge.py`，支持 `dotenv + OpenAI(base_url, api_key)`。
- `eval/run_eval.py` 接入 `--enable-llm-judge` 与缓存机制。
- `scripts/eval/*.sh` 支持环境变量开关 API Judge。

## M3（已完成）真实对齐训练入口
- 新增 `src/train/real_pref_train.py`（DPO/SimPO/KTO 实参训练）。
- `scripts/train/run_real_alignment_pipeline.sh` 支持 `ALIGNMENT_MODE=real`。
- `scripts/train/run_layer_b_real_sft.sh` 增加 OOM 自动降级重试。
- 全链路强制 `save_total_limit=2`。

## M4（已完成）小规模真实闭环验证
- Tiny 模型真实 SFT 训练跑通（loss/log/checkpoint/metrics）。
- Tiny 模型真实 DPO/SimPO/KTO 跑通（真实 backward、指标落盘）。
- 生成 loss 曲线与闭环报告。

## M5（下一步）论文主规模实验（7B/14B）
- 迁移到 Qwen2.5-7B（Layer-B）并复现同流程。
- 通过自动评测与消融选出最优配置。
- 扩展到 14B（Layer-C），产出论文主结果表。
