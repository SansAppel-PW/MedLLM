# Qwen7B Layer-B 阻塞报告

- 时间: 2026-02-26T03:45:31Z
- 状态: 当前环境无 `nvidia-smi`，无法执行 Qwen2.5-7B QLoRA 真实训练。
- 影响: Layer-B 主实验（Qwen7B）训练阶段被阻塞，但小规模真实闭环已完成，可作为迁移前验证层。

## 建议迁移配置
- 模型: `Qwen/Qwen2.5-7B-Instruct`
- 训练文件: `data/clean/real_sft_train.jsonl`
- 验证文件: `data/clean/real_sft_dev.jsonl`
- 推荐最小显存: >= 24GB (QLoRA 4bit, bs=1, grad_acc>=16)
- 启动命令:
```bash
bash scripts/train/run_layer_b_qwen_autofallback.sh
```

## 自愈策略
1. 首次尝试: max_length=2048, grad_acc=16
2. OOM 回退1: max_length=1536, grad_acc=32
3. OOM 回退2: max_length=1024, grad_acc=64
