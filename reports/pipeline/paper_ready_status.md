# Paper-Ready Pipeline Status

- Generated at (UTC): 2026-02-27T15:05:53Z
- Model target: `Qwen/Qwen2.5-7B-Instruct`
- Alignment mode: `real`

| Step | Status | Note |
|---|---|---|
| Data Build | SKIPPED | existing real dataset reused |
| Training | DONE | training fallback active (see resource_skip_report.md) |
| Evaluation | DONE | thesis evaluation assets refreshed |
| E2E Acceptance | DONE | demo e2e acceptance refreshed |
| Thesis Readiness | DONE | FAIL=0, DEFERRED=2 |

## Key Outputs
- `reports/real_dataset_report.md`
- `reports/alignment_compare.md`
- `reports/eval_default.md`
- `reports/sota_compare.md`
- `reports/error_analysis.md`
- `reports/detection_eval_v2_balanced.md`
- `reports/detection_eval_v2_hybrid_llm.md` (optional)
- `reports/detection_eval_llm_judge.md` (optional)
- `reports/thesis_assets/`
- `reports/e2e_acceptance.md`
- `reports/thesis_support/thesis_draft_material.md`
- `reports/thesis_support/benchmark_artifact_report.md`
- `reports/thesis_support/benchmark_artifact_report_v2_balanced.md`
- `reports/thesis_support/thesis_readiness.md`
