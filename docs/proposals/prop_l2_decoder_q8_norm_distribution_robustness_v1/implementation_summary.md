# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_q8_norm_distribution_robustness_v1`

## Scope
- Add a Layer 2 task-generator abstraction:
  `decoder_q8_normalization_distribution`.
- Reuse the existing q8 normalization frontier grid and estimator.
- Switch the dataset from prompt-stress to distribution robustness.
- Pass the bf16 reciprocal PPA artifact explicitly to the estimator.

## Files Changed
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`

## Local Validation
- `PYTHONPATH=/workspaces/RTLGen:/workspaces/RTLGen/control_plane /workspaces/RTLGen/control_plane/.venv/bin/python3 -m pytest -q control_plane/control_plane/tests/test_l2_task_generator.py tests/test_llm_decoder_q8_norm_frontier.py tests/test_llm_decoder_quantization_outline.py`
- `python3 -m py_compile control_plane/control_plane/services/l2_task_generator.py npu/eval/estimate_llm_decoder_q8_norm_frontier.py`

## Evaluation Request
- item: `l2_decoder_q8_norm_distribution_robustness_v1`
- evaluation mode: `broad_ranking`
- abstraction layer: `decoder_q8_normalization_distribution`
- dispatch target: remote evaluator `eval-daemon-b7c2d9c80c1c`
