# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- `title`: `Llama7B attention/KV compute floor gap`

## Scope
- Added and ran an L2 evaluator that reads merged compute-sensitivity,
  measured-compute, and measured-compute-partition artifacts.
- Reported MAC/cycle gap, MAC/cycle/mm2 gap, and required compute area fraction
  at the best measured compute density.
- Did not run synthesis, PnR, or detailed NoC simulation.

## Files Changed
- `npu/eval/estimate_llm_decoder_attention_kv_compute_floor_gap.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- `control_plane/control_plane/artifact_policy.py`
- `control_plane/control_plane/tests/test_l2_task_generator.py`
- `control_plane/control_plane/tests/test_artifact_policy.py`

## Local Validation
- `python3 npu/eval/estimate_llm_decoder_attention_kv_compute_floor_gap.py ...`
- `PYTHONPATH=/tmp/rtlgen-compute-floor-gap/control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest -q control_plane/control_plane/tests/test_artifact_policy.py control_plane/control_plane/tests/test_l2_task_generator.py::test_generate_l2_campaign_task_adds_decoder_attention_kv_compute_floor_gap control_plane/control_plane/tests/test_l2_task_generator.py::test_generate_l2_campaign_task_adds_decoder_attention_kv_physical_hbm_compute_sensitivity`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Evaluation Request
- requested task: `l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- cost class: low
- paired baseline: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`

## Risks
- The result depends on the planning-model HBM floor from PR #750.
- The measured compute density may improve with a purpose-built dense array,
  which is exactly the next question to test.
