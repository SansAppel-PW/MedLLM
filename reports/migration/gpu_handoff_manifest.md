# GPU Migration Handoff Manifest

- Generated at (UTC): 2026-02-27T14:20:20.146147+00:00
- Branch: `codex/worktree`
- Commit: `63abf7909260c0bcba60e0e5c52a61f921ec60e7`
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

## Critical Files
| path | exists | size_bytes | sha256 |
|---|---|---:|---|
| requirements.txt | True | 395 | c56bcc108b770dd0bd38cdc595d189d71130dc905d1ca1e05d304ffe5eafa2cd |
| Makefile | True | 938 | bd44485028c044a3f6e08fdfe367927f3a8de8085f2e658edb587a6c59f9a9c5 |
| README.md | True | 5976 | 33ccd35647677fae2ecce993d8c0fa39c65e7aeb9ffb360f1fd000d75d2af499 |
| docs/GPU_MIGRATION_RUNBOOK.md | True | 1920 | cd053627892582bb45fbb578290b338167709d9b32b4b736ac1278442ea85d56 |
| docs/RESOURCE_AWARE_EXECUTION.md | True | 1243 | 6aaeb99f3fa369e71bf466abf5cfd9265ffabc85a4c230bc67e8e39c796c0e1f |
| scripts/migration/bootstrap_gpu_env.sh | True | 1900 | d5a673a30bd46ea90fa00150ed672ada1137cb6f7d58ff52c8811be888a8971b |
| scripts/migration/run_gpu_thesis_experiment.sh | True | 4673 | ab3717779b04a15dfdbc757e8b8a5b1de996aeffab9231f3f6e91c5aedde496c |
| scripts/migration/check_handoff_readiness.py | True | 2145 | e5d3f79252df2313b2855f15eba69237872ffce2bb08f6562adaeb366cee7a94 |
| scripts/train/run_real_alignment_pipeline.sh | True | 12932 | e9c846d45efae5a4df9799085017357d079310e816bc8822709fd8f04eecb951 |
| scripts/train/run_layer_b_real_sft.sh | True | 3300 | a8d7c1704cbcd81575e3fbf32af023eda50182fa0ff5bdd2d2ee22a297577390 |
| scripts/eval/run_thesis_pipeline.sh | True | 5610 | e82114769021db15a05def4c8d45cd1923409cf5eaa2cf0a29f7c9a7b7e91b68 |
| scripts/pipeline/run_paper_ready.sh | True | 6337 | 8ade5bb39482c94e38eea63e5ef131920eb6a0fc94ffec0b506dc04ca9905d16 |
| configs/train/sft_layer_b_real.yaml | True | 997 | b9c8bcf277e83754bd8a71d3c005708de609d5a744d61477cb7690ff2a05d076 |
| configs/train/dpo_real.yaml | True | 381 | 06fde6f94dc6cea4b0cce0c2a875194859a94f1a1217502db3846735424aad1c |
| configs/train/simpo_real.yaml | True | 393 | a60726b2536f457c7fec02ed2126a561f37364551949a92119a5064a8170c9f9 |
| configs/train/kto_real.yaml | True | 383 | 5fa4f3f4d41c964ae7961e62882421f904dcb3a9d3f5e9290773eea8b91e1667 |
