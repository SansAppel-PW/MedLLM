# Stage 7：规则检测 + LLM 回退融合迭代（2026-02-26）

## 目标
- 在不增加 GPU 训练负担的前提下，提升 v2 去偏置基准上的检测可用性。
- 将“规则检测 + API 回退”的混合路径工程化为可选开关，纳入论文证据链。

## 代码改动
1. `src/detect/evaluate_detection.py`
- 新增可选参数：
  - `--enable-llm-fallback`
  - `--llm-model / --llm-cache / --llm-min-confidence / --llm-max-calls`
  - `--llm-trigger (pred_low | pred_low_or_medium)`
- 规则检测先运行；当预测为低风险时可触发 LLM 回退，按风险等级和置信度升级预测。
- 报告新增回退统计：调用次数、提升次数。

2. `scripts/eval/run_detection_robustness.sh`
- 新增 `ENABLE_V2_LLM_FALLBACK` 可选分支，输出：
  - `reports/detection_eval_v2_hybrid_llm.md`
  - `reports/detection_predictions_v2_hybrid_llm.jsonl`

3. `scripts/eval/run_thesis_pipeline.sh`
- 接入 v2 回退相关环境变量并透传到鲁棒性脚本。
- 论文草稿生成显式传入 v2/hybrid 报告路径。

4. 论文材料与文档
- `scripts/eval/generate_thesis_draft_material.py` 增加 v2-hybrid 指标写入。
- `README.md`、`scripts/pipeline/run_paper_ready.sh`、`scripts/eval/build_thesis_assets.py` 增加可选产物说明。

## 真实结果
### v2 规则基线（1200样本）
- Accuracy/F1: 0.5000 / 0.0000
- 报告：`reports/detection_eval_v2_balanced.md`

### v2 规则+LLM回退（80样本，缓存复用）
- Accuracy/F1: 0.7250 / 0.7609
- Recall: 0.8750
- 回退调用/提升: 80 / 52
- 报告：`reports/detection_eval_v2_hybrid_llm.md`

## 结论
- 规则检测在去偏置 benchmark 上泛化不足，但可通过 API 回退显著恢复可用性。
- 当前方案可作为“无显存扩容阶段”的工程可行解，后续可将 LLM 回退输出蒸馏为本地轻量分类器，降低在线 API 依赖。
