# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- Llama7B measured-compute clustered partition frontier.

## Scope
- Added a Layer 2 estimator that reuses merged corrected NPU compute PPA rows.
- Added clustered sequence-tile scheduling, local/shared SRAM residency shares, and NoC bandwidth/hop contention.
- Added a control-plane evidence hook for `decoder_attention_kv_measured_compute_partition`.
- Did not add new RTL/PPA, cycle-accurate NoC arbitration, or SRAM macro floorplanning.

## Files Changed
- `npu/eval/estimate_llm_decoder_attention_kv_measured_compute_partition.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_partition_llama7b_v1/*`

## Local Validation
- `python3 -m py_compile npu/eval/estimate_llm_decoder_attention_kv_measured_compute_partition.py control_plane/control_plane/services/l2_task_generator.py`
- Reduced smoke estimator run passed.
- Full local estimator run generated 672408 rows with 212112 skipped infeasible area/cluster rows.

## Evaluation Request
- `item_id`: `l2_decoder_attention_kv_measured_compute_partition_llama7b_v1`
- cost class: low Layer 2 campaign
- paired baseline: `l2_decoder_attention_kv_measured_compute_llama7b_v1`

## Risks
- NoC contention and SRAM residency remain planning assumptions.
- The best cluster count should be used to choose the next deeper RTL/PPA target, not as a final implementation claim.
