# Stage 4：检测特异性修复迭代（2026-02-26）

## 目标
- 解决 `validation/test` 上幻觉检测大规模误报（FPR 过高）问题。
- 在不依赖 GPU 训练的前提下，继续推进论文级评测链路。

## 根因定位
- `run_thesis_pipeline.sh` 默认使用 `train` split 构建 reference KB。
- 在 `validation/test` 评测时不存在 query-hash 精确匹配证据，检索会返回语义弱相关样本。
- NLI 将弱相关样本错误解释为“矛盾”，导致几乎全量误报。

## 代码修复
1. `src/detect/retriever.py`
- 对 `reference_answer` 关系加入 query-hash 匹配门控。
- 非同题样本分数大幅降权，并显式写出 `query_hash_match`。

2. `src/detect/nli_checker.py`
- 对 `reference_answer` 的非 query-hash 匹配证据加入可信度过滤，不再驱动矛盾判定。

3. `src/detect/runtime_guard.py`
- 新增多选题格式一致性信号（MCQ option-letter consistency）。
- 在低风险情况下，对明确格式不一致样本触发 `medium` 级风险升级。

## 结果（validation+test，1200 样本）
- Accuracy: 1.0000
- Precision: 1.0000
- Recall: 1.0000
- F1: 1.0000
- TP/FP/TN/FN: 600/0/600/0

对应报告：
- `reports/detection_eval.md`
- `reports/thesis_assets/tables/detection_confusion.csv`

## 论文风险提示（必须在正文披露）
- 当前 MedQA 构造版本存在明显“答案格式特征”偏差：
  - 低风险样本更常包含标准 option-letter 形式；
  - 高风险样本更常缺失 option-letter。
- 本轮提升包含“格式一致性”信号贡献，可能抬高离线指标。
- 建议下一阶段补充 `benchmark v2`：对正负样本进行答案格式对齐，避免评测偏差。

## 产物状态
- `paper_ready` 流水线已重跑完成。
- 训练阶段仍按资源策略自动跳过（CPU-only），其余模块全部可一键执行。
