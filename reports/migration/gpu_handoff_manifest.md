# GPU Migration Handoff Manifest

- Generated at (UTC): 2026-02-27T14:38:48.161026+00:00
- Branch: `codex/worktree`
- Commit: `fc190bda1d12c69eee5fc517c2d420fcb4c67de8`
- Worktree clean: `False`

## Target Run
- Model: `Qwen/Qwen2.5-7B-Instruct`
- Tier: `7b`
- Alignment mode: `real`
- Allow skip training: `false`

## Required Env
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`

## Commands
1. `bash scripts/migration/bootstrap_gpu_env.sh`
2. `MODEL_NAME='Qwen/Qwen2.5-7B-Instruct' MODEL_TIER='7b' bash scripts/migration/run_gpu_thesis_experiment.sh`
3. `python3 scripts/migration/check_gpu_completion.py`

## Critical Files
| path | exists | size_bytes | sha256 |
|---|---|---:|---|
| requirements.txt | True | 395 | c56bcc108b770dd0bd38cdc595d189d71130dc905d1ca1e05d304ffe5eafa2cd |
| Makefile | True | 1031 | de1cc685f57ee8a3f417aac4c22ab48a5f695ee14eda1a9cc8b30681012002fb |
| README.md | True | 6185 | 8e0b08d32f21d5e7e11ccfc424c28d341572c5c3f371661f741460794d727acb |
| docs/GPU_MIGRATION_RUNBOOK.md | True | 2274 | 53d2aaa34bdcff41341e50aee295aebd780a1624e531d69d40c46584023bf642 |
| docs/RESOURCE_AWARE_EXECUTION.md | True | 1243 | 6aaeb99f3fa369e71bf466abf5cfd9265ffabc85a4c230bc67e8e39c796c0e1f |
| scripts/migration/bootstrap_gpu_env.sh | True | 1900 | d5a673a30bd46ea90fa00150ed672ada1137cb6f7d58ff52c8811be888a8971b |
| scripts/migration/run_gpu_thesis_experiment.sh | True | 5214 | c2c5c495058d384894ebf1058fc26271e5a19cf62761582728cac2ec8ec5cb90 |
| scripts/migration/check_handoff_readiness.py | True | 2245 | 1b57b0e5c5b1eb40258fe02df42ec0fdabd6fed13fab82ba9be51182b98514c6 |
| scripts/migration/check_gpu_completion.py | True | 6377 | d581953d0ea64d292cf982d75dabaa4dc2c66b62927a789027ce020f37f23831 |
| scripts/train/run_real_alignment_pipeline.sh | True | 12932 | e9c846d45efae5a4df9799085017357d079310e816bc8822709fd8f04eecb951 |
| scripts/train/run_layer_b_real_sft.sh | True | 3300 | a8d7c1704cbcd81575e3fbf32af023eda50182fa0ff5bdd2d2ee22a297577390 |
| scripts/eval/run_thesis_pipeline.sh | True | 5610 | e82114769021db15a05def4c8d45cd1923409cf5eaa2cf0a29f7c9a7b7e91b68 |
| scripts/eval/analyze_llm_fallback_impact.py | True | 8501 | 18059866357f8f254d0d2cbcc2a872a9d5908ee9a4a86ae6f4e477d268fa7a25 |
| scripts/pipeline/run_paper_ready.sh | True | 6337 | 8ade5bb39482c94e38eea63e5ef131920eb6a0fc94ffec0b506dc04ca9905d16 |
| configs/train/sft_layer_b_real.yaml | True | 997 | b9c8bcf277e83754bd8a71d3c005708de609d5a744d61477cb7690ff2a05d076 |
| configs/train/dpo_real.yaml | True | 381 | 06fde6f94dc6cea4b0cce0c2a875194859a94f1a1217502db3846735424aad1c |
| configs/train/simpo_real.yaml | True | 393 | a60726b2536f457c7fec02ed2126a561f37364551949a92119a5064a8170c9f9 |
| configs/train/kto_real.yaml | True | 383 | 5fa4f3f4d41c964ae7961e62882421f904dcb3a9d3f5e9290773eea8b91e1667 |
