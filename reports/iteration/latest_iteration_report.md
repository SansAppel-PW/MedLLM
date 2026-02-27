# Loop Iteration Report

- 生成时间(UTC): 2026-02-27T22:56:55.958290+00:00

## 关键结果摘要
- train_loss: 10.734590888023376
- final_eval_loss: 10.736875534057617
- exact_match: 0.0
- rouge_l_f1: 0.0
- char_f1: 0.0

## 真实数据摘要
- real_train_count: 0
- real_dev_count: 0
- real_test_count: 0
- real_benchmark_count: 0

## 真实对齐摘要
- dpo_pair_count: 70054
- dpo_pref_accuracy_after: 0.662109375
- simpo_score_after: 0.640625
- kto_score_after: 0.689453125
- best_alignment_method: KTO
- best_alignment_score: 0.689453125

## Baseline 分层摘要
- baseline_real_mainline_count: 2
- baseline_proxy_background_count: 4

## 风险评估
- 技术风险（低）：对齐训练已覆盖真实 DPO/SimPO/KTO，闭环完整。 缓解：保持控制变量法迭代并扩充偏好数据规模，巩固统计显著性。
- 算力风险（高）：当前环境是否具备 CUDA 决定 Qwen7B 主实验能否执行。 缓解：使用 run_layer_b_qwen_autofallback.sh；无 GPU 输出 blocker，有 GPU 自动 OOM 回退。
- 数据风险（中）：small-real 当前样本规模小，不能用于论文主结论。 缓解：迁移到 real_* 数据并扩容后再产出主结果表与消融。
- 论文逻辑风险（中）：proxy 与 real 结果混写会导致证据链不可信。 缓解：继续保持分层目录与报告口径隔离。

## 论文贡献度评估（四问）
- 对应论文哪个章节/小节？ 第3章实验系统、第5章训练流程、第6章阶段性结果与风险。
- 是否产出论文可用图表/数据/表格？ 是，已产出 loss 曲线、eval 指标、run card、baseline 审计表，并补充 real alignment 指标。
- 是否增强创新性或严谨性？体现在哪里？ 主要增强严谨性：真实闭环证据链 + 自动回退 + blocker 可审计机制。
- 若不服务论文，是否降级为附录？ small-real fallback 结果降级为附录/工程验证，不作为主结论。

## 下一步最小闭环
- 在 GPU 环境运行 Qwen7B Layer-B 自动回退训练脚本并产出真实 loss/ckpt/eval。
- 保持真实 DPO，继续扩容偏好对并执行至少 1 组 real-alignment 消融。
- 更新 baseline 对比表为“真实主结果 + 代理背景”双层表述。
