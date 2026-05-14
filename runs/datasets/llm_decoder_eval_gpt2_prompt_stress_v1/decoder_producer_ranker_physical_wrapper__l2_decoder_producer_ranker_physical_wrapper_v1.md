# Decoder Producer/Ranker Physical Wrapper

- model: `decoder_producer_ranker_physical_wrapper_v1`
- target: `r64_k1_nm16_ready_valid_physical_wrapper`
- decision: `producer_ranker_physical_wrapper_measured`
- next_step: Use this wrapper PPA as the first measured producer-ranker integration point and then compare r128 or producer-coupled variants.

## Checks

| check | passed | observed |
|---|---|---|
| ready_valid_equivalence_predecessor_passed | `True` | `ready_valid_equivalence_passed` |
| physical_wrapper_rtl_materialized | `True` | `['runs/designs/activations/decoder_r64_k1_producer_ranker_physical_wrapper/verilog/candidate_stream_merge_fifo_k1_l16_t16_d16.v', 'runs/designs/activations/decoder_r64_k1_producer_ranker_physical_wrapper/verilog/decoder_r64_k1_producer_ranker_physical_wrapper.v', 'runs/designs/activations/decoder_r64_k1_producer_ranker_physical_wrapper/verilog/logit_rank_r64_l16_k1.v']` |
| physical_sweep_completed_with_metrics | `True` | `{'synthesis_status': 'ok', 'metrics_status': 'ok'}` |

## Metrics

- status: `ok`
- critical_path_ns: `32.244646582551134`
- die_area: `810000.0`
- total_power_mw: `1.82241`
- result_path: ``

## Synthesis

- status: `ok`
- log_path: `control_plane/runtime_logs/decoder_producer_ranker_physical_wrapper/decoder_r64_k1_producer_ranker_physical_wrapper_3_3_place_gp.log`
