# 开题要求深度一致性审计报告

- PASS: 3
- PARTIAL: 0
- FAIL: 0

| ID | 要求 | 状态 | 结论 | 证据 |
|---|---|---|---|---|
| C1 | 真实数据集规模与来源可审计 | PASS | train/dev/test=70054/8755/8755, benchmark=12998, source=unified, source_requirements=True | data/clean/real_sft_train.jsonl<br>reports/real_dataset_summary.json<br>【DOCX | 三、课题技术路线及研究方案 | 段落#T03R01C01】 |
| C2 | RAG流程与知识图谱构建对齐开题描述 | PASS | cm3kg_core_kb=180000, merged_kb=180800, pipeline_merge_support=True | data/kg/cm3kg_core_kb.jsonl<br>data/kg/real_medqa_reference_kb_merged.jsonl<br>scripts/eval/run_thesis_pipeline.sh<br>【DOCX | 三、课题技术路线及研究方案 | 段落#T03R01C01】 |
| C3 | 从数据到结论端到端流程可复现并与课题一致 | PASS | missing_scripts=0, closure_fail=0, A10=PASS | scripts/data/ensure_real_dataset.sh<br>scripts/train/run_gpu_thesis_mainline.sh<br>scripts/eval/run_thesis_pipeline.sh<br>scripts/audit/build_thesis_ready_package.py<br>reports/gpu_experiment_closure.json |
