# Quality Gate

- Distribution manifest exists at
  `runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json`.
- Sample set has at least 12 prompt-regime rows.
- The evaluator must generate distribution reference and candidate manifests
  before validating the contract.
- The sweep artifact must include `distribution` rollups for each template row.
- The sweep artifact must include the distribution-dependence `scope_note`.
- `scripts/validate_runs.py --skip_eval_queue` must pass before submission.
