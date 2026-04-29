# Quality Gate

## Required Checks

- `python3 -m py_compile npu/eval/sweep_llm_decoder_candidate_quality.py`
- `PYTHONPATH=control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -q`
- `python3 scripts/validate_runs.py --skip_eval_queue`
- Local rough-grid smoke:
  - `python3 npu/eval/sweep_llm_decoder_candidate_quality.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json --rough-grid decoder_probability_broad_v1 --out-dir /tmp/decoder_probability_broad_grid --out /tmp/decoder_probability_broad_grid.json`

## Acceptance

- The evaluator result must include `decoder_quality_sweep__l2_decoder_probability_sensitivity_v1.json`.
- The artifact must include `scope_note` stating the distribution-dependence
  limitation.
- The result must list per-template next-token/top-k rates and sample-level miss
  IDs.
