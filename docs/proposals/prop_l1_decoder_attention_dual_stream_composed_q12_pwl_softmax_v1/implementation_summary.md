# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_v1`
- title: Composed dual-stream attention q12/PWL softmax datapath

## Scope
- Added `pwl_recip_lut` support to the composed dual-stream attention RTL generator.
- Parameterized composed softmax score and weight row widths.
- Updated the composed datapath guard to validate q12/PWL reciprocal softmax structure.
- Added one full-size q12/PWL composed design config and one matching Nangate45 sweep.

## Files Changed
- `npu/rtlgen/gen_attention_dual_stream_composed.py`
- `npu/eval/check_attention_dual_stream_composed_guard.py`
- `tests/test_attention_dual_stream_composed_generator.py`
- `runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12/config.json`
- `runs/campaigns/npu/attention_dual_stream_composed_v1/sweeps/nangate45_dual_stream_composed_hier_q12_pwl.json`

## Local Validation
- `PYTHONPATH=. pytest -q tests/test_attention_dual_stream_composed_generator.py`
- `PYTHONPATH=.:control_plane pytest -q control_plane/control_plane/tests/test_l1_task_generator.py -k 'attention_dual_stream_composed_configs'`
- `PYTHONPATH=.:control_plane python3 scripts/validate_runs.py --skip_eval_queue`
- Full-size q12/PWL generated RTL passed `check_attention_dual_stream_composed_guard.py` and iverilog elaboration.

## Evaluation Request
- Measure `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`.
- Compare against `l1_decoder_attention_dual_stream_composed_softmax_recip_lut_ppa_v1_r3` and the L2 q8 reciprocal-LUT composed frontier.

## Risks
- This is a PPA measurement for a safer softmax datapath, not final Llama7B checkpoint quality evidence.
- A follow-on L2 result must substitute the measured q12/PWL composed metrics into the Llama7B schedule before promotion.
