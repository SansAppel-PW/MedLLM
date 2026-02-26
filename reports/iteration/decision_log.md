# Decision Log

| 记录时间(UTC) | Run Tag | real train/dev/test | DPO 对数 | 最优对齐 | 决策 |
|---|---|---|---:|---|---|
| 2026-02-26T04:38:59.450493+00:00 | small_real_lora_v13 | 288/36/36 | 288 | SimPO | 保持 real-data + real-DPO 路径，下一步优先申请 GPU 推进 Layer-B Qwen7B 主实验。 |

## Latest Decision
- 保持 real-data + real-DPO 路径，下一步优先申请 GPU 推进 Layer-B Qwen7B 主实验。

## Next Minimal Loop
- 在 GPU 环境运行 Qwen7B Layer-B 自动回退训练脚本并产出真实 loss/ckpt/eval。
- 保持真实 DPO，继续扩容偏好对并执行至少 1 组 real-alignment 消融。
- 更新 baseline 对比表为“真实主结果 + 代理背景”双层表述。
