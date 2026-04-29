# Quality Gate

- Prompt-stress manifest exists at
  `runs/datasets/llm_decoder_eval_tiny_v1/manifest_prompt_stress_v1.json`.
- Sample set has 24 prompt-stress rows.
- The evaluator must generate prompt-stress reference and candidate manifests
  before validating the contract.
- The sweep must use `decoder_survivor_prompt_stress_v1`.
- The sweep artifact must include `distribution` rollups for each template row.
- `scripts/validate_runs.py --skip_eval_queue` must pass before submission.
