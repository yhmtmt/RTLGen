# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_compute_llama7b_v1`
- Llama7B quality-backed KV8 measured-compute substitution

## Scope
- Added a Layer 2 estimator that reads merged corrected NPU compute PPA rows and converts measured block area, delay, power, and `num_modules` into die-budgeted compute replica counts.
- Added a control-plane evidence hook for `decoder_attention_kv_measured_compute`.
- Added proposal/evaluation docs for the Llama7B 131k native-GQA KV8 measured-compute substitution job.
- Did not add new RTL/PPA runs, SRAM macro modeling, or cycle-accurate NoC arbitration.

## Files Changed
- `npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_llama7b_v1/*`

## Local Validation
- `python3 -m py_compile npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py control_plane/control_plane/services/l2_task_generator.py`
- `python3 npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py ... --out /tmp/rtlgen_measured_compute_full.json --out-md /tmp/rtlgen_measured_compute_full.md`
- Full local sweep generated 12,480 rows; all rows were `tile_attention` dominated under measured compute PPA.

## Evaluation Request
- `item_id`: `l2_decoder_attention_kv_measured_compute_llama7b_v1`
- cost class: low Layer 2 campaign
- paired baseline: `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v1`
- DB dependencies are limited to recently merged corrected-compute items; older L2 HBM/memory-NoC evidence is referenced as materialized repo artifacts because those historical work items are not present in the rebuilt control-plane DB.

## Risks
- Vector throughput remains a ratio assumption tied to MAC throughput.
- The result is a planning estimate until selected tiled compute, SRAM, NoC, and dispatcher points receive deeper RTL/PPA or detailed service modeling.
