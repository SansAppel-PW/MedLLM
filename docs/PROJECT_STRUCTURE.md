# Project Structure (Paper-Ready Mainline)

本项目当前按“可迁移到 GPU 后一键复现实验”组织，主链目录如下。

## 1. Core Runtime
- `src/data/`：数据治理与清洗核心逻辑。
- `src/detect/`：医疗幻觉检测（白盒 + 检索 + 可选 LLM 回退）。
- `src/train/`：真实 SFT 与真实偏好对齐训练（DPO/SimPO/KTO）。
- `src/serve/`：服务与推理入口。

## 2. Orchestration Scripts
- `scripts/data/`：真实数据构建、benchmark 构建、治理流水线。
- `scripts/train/`：Layer-B 真实 SFT 与真实对齐编排。
- `scripts/eval/`：主评测、鲁棒评测、论文资产生成。
- `scripts/pipeline/run_paper_ready.sh`：本地一键论文流水线。
- `scripts/migration/`：GPU 迁移、环境 bootstrap、严格完工校验。

## 3. Config & Evaluation
- `configs/train/`：SFT/DPO/SimPO/KTO 训练配置。
- `configs/eval/`：评测配置。
- `eval/`：统一评测器与 LLM-as-a-Judge 实现。

## 4. Deliverables
- `reports/training/`：训练指标与资源探测。
- `reports/thesis_support/`：论文初稿支撑材料与就绪度审计。
- `reports/thesis_assets/`：表格、图、案例。
- `reports/migration/`：GPU 交接清单与完工校验。

## 5. Non-Core Policy
- 历史 tiny/proxy 试验残留与阶段性临时报告已清理，不再作为主链证据。
- 当前主链只保留可支撑 Qwen2.5-7B/14B 或 Qwen3 小参数真实训练与论文写作的资产。

## 6. High-Level Guides
- `docs/USAGE_MANUAL_FULL.md`：完整使用说明（含 GPU 一键执行路径）。
- `docs/PROJECT_MASTER_DOSSIER.md`：项目总档案（项目详情+使用说明+产出说明+论文章节草稿）。
- `reports/thesis_support/thesis_writing_material_full.md`：论文写作材料（章节、结果、模板）。
- `day1_run.sh`：GPU 首次上线“零思考”单文件执行脚本。
