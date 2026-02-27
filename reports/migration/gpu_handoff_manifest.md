# GPU Migration Handoff Manifest

- Generated at (UTC): 2026-02-27T15:24:47.970693+00:00
- Branch: `codex/worktree`
- Commit: `b3e76e176c1dcb2470afdddd5145d5fc59b995a5`
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
| Makefile | True | 1069 | a4d6bb6f9f8d55d510e19964732200cd2896c12d48f3566c004415f9e1067a6f |
| README.md | True | 6675 | 28592d7c481a2b41d1892eb9c5c5b21f39bdb68c5a69bc73735f67ed873965cb |
| day1_run.sh | True | 5888 | dd46ee498c6ab770fbbeed868bde00e4c9d3b00258efa42ca7bd89ef7986007e |
| docs/GPU_MIGRATION_RUNBOOK.md | True | 2393 | c7b38e6e10e78a798a7ef50cbc62f490747ece3d33e2c14f51290e49e98c7590 |
| docs/USAGE_MANUAL_FULL.md | True | 5129 | 52ad9306fec3f9f734f59e9101ba5f1ff4765a3ead34d81e36c04b5f3c6ea019 |
| docs/RESOURCE_AWARE_EXECUTION.md | True | 1243 | 6aaeb99f3fa369e71bf466abf5cfd9265ffabc85a4c230bc67e8e39c796c0e1f |
| scripts/migration/bootstrap_gpu_env.sh | True | 1900 | d5a673a30bd46ea90fa00150ed672ada1137cb6f7d58ff52c8811be888a8971b |
| scripts/migration/run_gpu_thesis_experiment.sh | True | 5718 | 650821010b6e4442e85fbada99653f114d1b114183efb4e0cfea8103a7f7b5ae |
| scripts/migration/check_handoff_readiness.py | True | 2297 | e0db4b5efcfa98dc2afc0eed04408fba609809bd9aad26bacc5b263821a612dc |
| scripts/migration/check_gpu_completion.py | True | 6377 | d581953d0ea64d292cf982d75dabaa4dc2c66b62927a789027ce020f37f23831 |
| scripts/train/run_real_alignment_pipeline.sh | True | 12932 | e9c846d45efae5a4df9799085017357d079310e816bc8822709fd8f04eecb951 |
| scripts/train/run_layer_b_real_sft.sh | True | 3300 | a8d7c1704cbcd81575e3fbf32af023eda50182fa0ff5bdd2d2ee22a297577390 |
| scripts/eval/run_thesis_pipeline.sh | True | 5610 | e82114769021db15a05def4c8d45cd1923409cf5eaa2cf0a29f7c9a7b7e91b68 |
| scripts/eval/analyze_llm_fallback_impact.py | True | 8874 | ad3bfe647b687873ce891f507561bb38db382bf4afc36cdb45c8bbe6431351f9 |
| scripts/pipeline/run_paper_ready.sh | True | 6337 | 8ade5bb39482c94e38eea63e5ef131920eb6a0fc94ffec0b506dc04ca9905d16 |
| configs/train/sft_layer_b_real.yaml | True | 997 | b9c8bcf277e83754bd8a71d3c005708de609d5a744d61477cb7690ff2a05d076 |
| configs/train/dpo_real.yaml | True | 381 | 06fde6f94dc6cea4b0cce0c2a875194859a94f1a1217502db3846735424aad1c |
| configs/train/simpo_real.yaml | True | 393 | a60726b2536f457c7fec02ed2126a561f37364551949a92119a5064a8170c9f9 |
| configs/train/kto_real.yaml | True | 383 | 5fa4f3f4d41c964ae7961e62882421f904dcb3a9d3f5e9290773eea8b91e1667 |
