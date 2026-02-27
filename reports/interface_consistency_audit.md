# Pipeline Interface Consistency Audit

- PASS: 6
- FAIL: 0

| ID | Requirement | Status | Detail | Evidence |
|---|---|---|---|---|
| C01 | GPU 主链关键脚本存在 | PASS | 关键脚本齐全。 | scripts/train/run_gpu_thesis_mainline.sh<br>scripts/train/run_real_alignment_pipeline.sh<br>scripts/train/run_layer_b_real_sft.sh<br>scripts/eval/run_thesis_pipeline.sh<br>scripts/eval/run_eval.sh<br>scripts/data/ensure_real_dataset.sh |
| C02 | Makefile 引用的脚本路径有效 | PASS | Makefile 脚本引用路径均存在。 | Makefile |
| C03 | 关键流水线脚本不得硬编码 python3 | PASS | 关键流水线脚本均通过 PYTHON_BIN 调用 Python。 | scripts/train/run_gpu_thesis_mainline.sh<br>scripts/train/run_real_alignment_pipeline.sh<br>scripts/train/run_layer_b_real_sft.sh<br>scripts/eval/run_thesis_pipeline.sh<br>scripts/eval/run_eval.sh |
| C04 | gpu-mainline 向子流水线透传 PYTHON_BIN | PASS | 已向 alignment 与 thesis eval 子流水线透传 PYTHON_BIN。 | scripts/train/run_gpu_thesis_mainline.sh |
| C05 | real-alignment 调用 Layer-B SFT 时透传 PYTHON_BIN | PASS | Layer-B SFT 子脚本透传 PYTHON_BIN 已配置。 | scripts/train/run_real_alignment_pipeline.sh<br>scripts/train/run_layer_b_real_sft.sh |
| C06 | Makefile 提供 GPU 一键主链入口与验收入口 | PASS | GPU 一键执行与验收目标齐全。 | Makefile |
