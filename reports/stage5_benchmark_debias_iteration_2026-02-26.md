# Stage 5：去偏置基准与鲁棒性评测迭代（2026-02-26）

## 本轮目标
- 消除 `real_medqa_benchmark` 中“答案格式与标签耦合”偏差。
- 将偏差审计与鲁棒性评测纳入默认论文流水线。

## 新增模块
1. `scripts/data/build_balanced_detection_benchmark.py`
- 自动解析 MCQ 选项并重写正负样本答案为统一格式：`正确答案: <选项字母>. <选项文本>`。
- 产出：`data/benchmark/real_medqa_benchmark_v2_balanced.jsonl`（本地生成，不入库）。
- 统计：3600 样本中重写 1798 条，仅 2 条未解析。

2. `scripts/eval/run_detection_robustness.sh`
- 自动串联：v2 构建 -> v2 参考 KB 构建 -> v2 检测评测 -> v2 偏差审计。

3. 流水线接入
- `scripts/eval/run_thesis_pipeline.sh` 默认启用 `RUN_BALANCED_DETECTION_AUDIT=true`。
- `scripts/eval/generate_thesis_draft_material.py` 增加 v2 偏差与 v2 检测指标写入。
- `scripts/audit/check_thesis_readiness.py` 增加 v2 偏差隔离判定逻辑（R7）。
- `scripts/pipeline/run_paper_ready.sh` 与 `README.md` 同步新增 v2 产物清单。

## 关键结果
### 原始 benchmark（validation+test）
- 偏差审计：`HIGH`，option-letter gap = `0.9917`
- 检测指标：Accuracy/F1 = `1.0000/1.0000`（受构造偏差影响）

### v2 去偏置 benchmark（validation+test）
- 偏差审计：`LOW`，option-letter gap = `0.0000`
- 检测指标：Accuracy/F1 = `0.5000/0.0000`
- 结论：当前检测策略对格式捷径敏感，去偏后泛化不足。

## 论文可用结论
- 已形成“偏差识别 -> 基准去偏 -> 鲁棒性复评”完整证据链。
- 论文中可明确声明：原始高分存在格式泄露；v2 结果更真实反映模型能力边界。

## 完整度状态
- `paper-ready` 已重跑，`thesis_readiness` 当前：`PASS=6, DEFERRED=1, FAIL=0`。
- 唯一 deferred 项为真实 7B 训练（受当前显存/设备限制，已有跳过证据和一键恢复路径）。
