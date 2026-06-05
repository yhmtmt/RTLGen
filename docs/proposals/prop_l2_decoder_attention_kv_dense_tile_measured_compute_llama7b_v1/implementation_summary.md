# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- title: Llama7B dense tile measured compute substitution

## Scope
- Added a dense-tile compute source to the measured-compute estimator.
- Added a control-plane L2 abstraction that dispatches the dense-tile
  substitution job.
- Did not add new physical synthesis points.
- Did not change SRAM/NoC service assumptions.

## Files Changed
- `npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- proposal metadata under this directory

## Local Validation
- Dense-tile estimator smoke passed and selected `dense_gemm_16x8_k1_p1` at
  1200 mm2 / 40% SRAM / 40% logic in the local run.
- Legacy measured-compute estimator smoke passed.
- `PYTHONPATH=/tmp/rtlgen-dense-scale-consumer/control_plane /workspaces/RTLGen/control_plane/.venv/bin/python -m pytest control_plane/control_plane/tests/test_l2_task_generator.py -q`
  passed with 93 tests.
- `python3 scripts/validate_runs.py --skip_eval_queue` passed.

## Evaluation Request
- item_id: `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- task_type: `l2_campaign`
- evaluation_mode: `frontier_detail`
- baseline: `l2_decoder_attention_kv_measured_compute_llama7b_v1`
- cost class: medium

## Risks
- Dense tile replica scaling does not include global command distribution or
  placement overhead for many replicas.
- Vector throughput is still tied to MAC throughput by assumption.
- SRAM service and NoC arbitration remain model terms.
