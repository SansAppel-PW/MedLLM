# Stage 6：LLM 风险评测基线迭代（2026-02-26）

## 目标
- 在无 GPU 训练条件下，新增可执行的 API 风险评测基线，补充论文证据维度。
- 与 v2 去偏置 benchmark 联动，验证系统在去捷径条件下的上限参考。

## 新增能力
1. `eval/llm_risk_judge.py`
- 实现 LLM-as-a-Judge 风险分类（high/medium/low），支持缓存与重试。
- 使用 `.env` 中 `OPENAI_BASE_URL` / `OPENAI_API_KEY` 注入，不硬编码密钥。

2. `scripts/eval/run_detection_llm_judge.py`
- 统一 benchmark + split 过滤 + 指标统计 + JSONL/Markdown 报告。

3. 流水线接入
- `scripts/eval/run_thesis_pipeline.sh` 增加可选开关：
  - `ENABLE_LLM_RISK_JUDGE=true`
  - `LLM_RISK_MODEL` / `LLM_RISK_MAX_SAMPLES` / `LLM_RISK_CACHE`
- `scripts/eval/generate_thesis_draft_material.py` 自动读取 `detection_eval_llm_judge.md` 指标。

## 本轮真实结果（v2 benchmark，80样本）
- 报告：`reports/detection_eval_llm_judge.md`
- Accuracy: 0.7250
- Precision: 0.6731
- Recall: 0.8750
- F1: 0.7609

## 结论
- 相比规则检测器在 v2 上的 F1=0.0000，LLM 风险评测基线已显著提升去偏置场景识别能力。
- 可在论文中作为“资源受限下的可行增强路径”和“后续蒸馏目标上界参考”。

## 当前整体状态
- thesis_readiness: PASS=6, DEFERRED=1, FAIL=0
- 唯一 deferred 仍为真实 7B 训练（硬件资源限制）。
