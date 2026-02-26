# 训练跳过报告

- 时间: 2026-02-26T03:48:38Z
- 模型: `Qwen/Qwen2.5-7B-Instruct`
- 模型层级: `7b`
- 跳过原因: Insufficient CUDA resources for 7B (need >= 18GB).
- 资源探测: `reports/training/resource_preflight.json`

## 后续动作
1. 扩容到可用 CUDA 显存后，重新运行：
   `ALIGNMENT_MODE=real MODEL_NAME=Qwen/Qwen2.5-7B-Instruct bash scripts/train/run_real_alignment_pipeline.sh`
2. 当前其余模块可继续执行，不阻塞评测与论文素材构建。
