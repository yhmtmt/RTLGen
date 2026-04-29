# Implementation Summary

- Added `npu/eval/estimate_llm_decoder_survivor_cost.py`.
- Added `decoder_survivor_cost_proxy` evidence generation to the L2 task
  generator.
- Added tests for the cost proxy and task-generator command wiring.

## Local Preview

The local preview ranks `grid_approx_pwl_bf16_path` and
`grid_approx_pwl_in_q8_w_q8_norm_exact` as the immediate exact-safe PWL frontier.
The proxy blocks q6/q4 rows from narrowing because they are not 24/24
next-token exact on the prompt-stress set.

## Verification

- `python3 -m py_compile npu/eval/estimate_llm_decoder_survivor_cost.py control_plane/control_plane/services/l2_task_generator.py`
- `PYTHONPATH=control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest tests/test_llm_decoder_survivor_cost.py control_plane/control_plane/tests/test_l2_task_generator.py -q`
- `python3 npu/eval/estimate_llm_decoder_survivor_cost.py --sweep runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_survivor_prompt_stress_v1.json --out /tmp/decoder_survivor_cost_proxy.json --out-md /tmp/decoder_survivor_cost_proxy.md`
