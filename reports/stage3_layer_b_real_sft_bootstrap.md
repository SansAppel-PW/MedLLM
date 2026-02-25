# Stage 3.1 模块报告：Layer-B 真实 SFT 训练闭环骨架

## 1. 阶段启动风险评估（执行前）
- 技术风险：真实训练依赖链复杂（torch/transformers/peft/datasets/bitsandbytes），环境差异会导致脚本不可运行。
  - 缓解：在入口脚本中做依赖前置检查，缺失时给出明确安装提示。
- 计算资源风险：7B 真实训练需要 GPU 显存与训练时长保障。
  - 缓解：默认 QLoRA + 4bit，优先建立小规模真实闭环。
- 论文逻辑风险：若只交付脚本而不落盘可复现元数据，证据链不完整。
  - 缓解：强制输出 `run_manifest.json`、`metrics.json`、`train_log.jsonl`。
- 数据质量风险：真实数据文件可能缺失或 split 不规范。
  - 缓解：入口阶段强校验 train/dev 文件存在性，并在 manifest 记录哈希。
- 时间成本风险：若直接扩展到 14B 会压缩验证窗口。
  - 缓解：先固定 Layer-B（7B）闭环，再升级 Layer-C（14B）。

## 2. 本模块落地产物
- 真实训练入口：`src/train/real_sft_train.py`
- Layer-B 配置：`configs/train/sft_layer_b_real.yaml`
- Layer-B 启动脚本：`scripts/train/run_layer_b_real_sft.sh`
- 文档更新：`README.md`、`requirements.txt`
- 轻量测试：`tests/test_real_sft_cli.py`

## 3. 可复现证据链设计
- 运行元信息：`run_manifest.json`
  - commit hash、命令行、模型名、seed、数据哈希、样本数、输出路径
- 训练过程日志：`train_log.jsonl`
- 结果指标：`metrics.json` 与对外摘要 `metrics_out`
- 配置快照：`config_snapshot.yaml`（若传入 `--config`）

## 4. 本模块论文影响评估
1. 属于论文章节：`第5章 模型训练与对齐实验`。
2. 是否能形成完整实验小节：能（“真实SFT训练流程与复现机制”）。
3. 是否增强论文创新性：中等增强（创新点不在训练器本身，在于系统化证据链与后续对齐实验承接）。
4. 是否增强论文严谨性：显著增强（从代理训练转向真实训练骨架，满足可复现性要求）。

结论：保留并作为 DPO/SimPO/KTO 真实化改造的基座模块。
