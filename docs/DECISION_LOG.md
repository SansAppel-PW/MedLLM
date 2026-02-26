# Decision Log

## 2026-02-26 | D001 | Small Real 闭环先于 Qwen7B
- 背景：开题目标要求三层闭环与真实训练证据链，但当前执行环境无 CUDA，且网络访问模型仓库不稳定。  
  `【DOCX | 三、课题技术路线及研究方案 | 段落#T03R001】` `【PDF | 页码p13 | 段落/条目#PG013L001】`
- 决策：先完成 Small Real 真实训练闭环（离线缓存小模型 + LoRA），并把 Qwen7B/14B 迁移为下一阶段目标。
- 理由：
  1. 保证真实 forward/backward、loss、checkpoint、eval、run card 证据链先落地；
  2. 避免在算力受限场景下阻塞整个论文工程推进；
  3. 保持与开题“三层实验结构”一致：先 Small Real，再 Full。  
     `【PDF | 页码p10 | 段落/条目#PG010L001】`
- 产物：
  - `scripts/train/run_small_real_pipeline.sh`
  - `reports/small_real/`（指标、图表、run card、结论）
  - `reports/training/small_real_lora_v3_metrics.json`

## 2026-02-26 | D002 | 训练脚本兼容 transformers 4.x/5.x
- 背景：环境安装到 transformers 5.2 后，`TrainingArguments` 和 `Trainer` 参数发生不兼容。
- 决策：在 `src/train/real_sft_train.py` 中加入动态签名兼容与 CPU 自愈降级（禁 4bit、8bit optim fallback、bf16/fp16 fallback）。
- 理由：
  1. 保持脚本跨环境可运行；
  2. 让失败路径自动降级，而不是中断流程；
  3. 对论文复现实验更稳健。
- 产物：
  - `src/train/real_sft_train.py`（兼容逻辑 + 环境快照写入 manifest）

## 2026-02-26 | D003 | Qwen7B Layer-B 采用“自动回退 + 阻塞报告”机制
- 背景：开题主线模型应以 Qwen2.5-7B/14B 为核心，但当前环境无 GPU。
- 决策：新增 `run_layer_b_qwen_autofallback.sh`，有 GPU 时自动做 OOM 级联回退；无 GPU 时生成阻塞报告并退出 0。
- 理由：
  1. 不中断总流水线推进；
  2. 保留“扩容后可一键重启”的工程状态；
  3. 与开题的 Layer-B 主实验路径保持一致。  
     `【PDF | 页码p12 | 段落/条目#PG012L001】` `【DOCX | 四、工作进度安排 | 段落#T04R001】`
- 产物：
  - `scripts/train/run_layer_b_qwen_autofallback.sh`
  - `configs/train/sft_layer_b_qwen7b_qlora.yaml`
  - `reports/small_real/qwen_layer_b_blocker.md`

## 2026-02-26 | D004 | 数据不入库改造：Git 去追踪 + 缺失自愈 Bootstrap
- 背景：当前仓库历史中 `data/` 目录存在被跟踪文件，违反“医学数据不入 GitHub”的强约束；同时 fresh clone 场景需要最小资产自愈以维持可运行。
  `【DOCX | 研究方案与技术路线 | 段落#T03R002】` `【PDF | 页码p10 | 段落/条目#PG010L002】`
- 决策：对 `data/` 下非 `.gitkeep` 文件执行 `git rm --cached`，并新增 `scripts/data/bootstrap_minimal_assets.py` 仅在缺失时生成最小 synthetic 资产（schema/kg/benchmark）。
- 理由：
  1. 把数据资产与代码资产彻底隔离，符合 Repo Safety Guard 约束；
  2. 避免运行链路依赖已入库数据，保证“无数据入库”下仍可一键闭环；
  3. 为后续真实数据下载/构建保留标准入口，不破坏论文证据链。
- 产物：
  - `scripts/data/bootstrap_minimal_assets.py`
  - `reports/data_bootstrap_report.md`
  - `reports/data_bootstrap_manifest.json`
  - `scripts/data/run_data_governance_pipeline.py`（接入 bootstrap）
  - `data/*` tracked 文件去追踪（cached remove）

## 2026-02-26 | D005 | 论文写作资产自动打包（主结果/消融/证据入口）
- 背景：在 Qwen7B 受算力阻塞时，仍需持续交付可直接用于论文撰写的结构化资产，避免“能跑但不可写”。
  `【DOCX | 研究目标与预期成果 | 段落#T02R003】` `【PDF | 页码p14 | 段落/条目#PG014L001】`
- 决策：新增 `build_thesis_ready_package.py`，按最新 small-real 结果自动产出主结果表、消融表、证据索引与论文局限性段落草稿。
- 理由：
  1. 让每轮迭代都直接沉淀论文可用资产；
  2. 保持“训练阻塞时其余模块仍前进”的自治策略；
  3. 缩短实验到写作的转换成本。
- 产物：
  - `scripts/audit/build_thesis_ready_package.py`
  - `reports/thesis_assets/tables/main_results_small_real.csv`
  - `reports/thesis_assets/tables/ablation_small_real_runs.csv`
  - `reports/thesis_assets/thesis_ready_summary.{md,json}`
