# Decoder Serial LPC1 Producer-Coupled Wrapper

- model: `decoder_serial_lpc1_producer_coupled_wrapper_v1`
- decision: `serial_lpc1_producer_coupled_wrapper_promoted`
- producer_ii_cycles: `384`
- critical_path_ns: `2.864771333952124`
- placed_cell_area_um2: `19304.684`
- total_power_mw: `0.0065519`
- next_step: Use serial_lpc1 as the ranker block in the next output-projection producer wrapper. The next open architectural risk is replacing the analytical producer cadence with measured producer output statistics or a resident-weight producer model.

## Checks

| check | passed | observed |
|---|---|---|
| selected_variant_exists | `True` | `decoder_r64_k1_serial_rank_lpc1_wrapper` |
| selected_variant_has_physical_metrics | `True` | `{'critical_path_ns': 2.864771333952124, 'die_area_um2': 810000.0, 'placed_cell_area_um2': 19304.684, 'total_power_mw': 0.0065519, 'stage_elapsed_seconds': 45.66, 'metrics_status': 'ok', 'design_dir': 'runs/designs/activations/decoder_r64_k1_serial_rank_lpc1_wrapper', 'top': 'decoder_r64_k1_serial_rank_lpc1_wrapper'}` |
| service_compatibility_selected_lowest_power | `True` | `{'coupled_extra_cycles_after_producer': 65, 'coupled_latency_us_per_token': 1205.855, 'coupled_total_cycles': 1205855, 'hidden_size': 768, 'integration': 'single_r64_ranker', 'macs_per_cycle': 8192, 'max_ranker_wait_cycles': 0, 'memory_bandwidth_bytes_per_cycle': 64.0, 'producer_done_cycles': 1205790, 'producer_ii_cycles': 1536, 'producer_lanes': 64, 'producer_latency_cycles': 30, 'producer_latency_us_per_token': 1205.79, 'ranker': 'serial_lpc1', 'ranker_critical_path_ns': 2.864771333952124, 'ranker_family': 'serial_running_best', 'ranker_instances': 1, 'ranker_pipeline_tail_cycles': 0, 'ranker_placed_cell_area_um2': 19304.684, 'ranker_service_cycles_per_producer_tile': 65, 'ranker_tile_service_cycles': 65, 'ranker_total_power_mw': 0.0065519, 'ranker_utilization': 0.042318, 'scenario': 'shared_gemm_stage_serial', 'service_limiter': 'weight_memory', 'throughput_margin_cycles': 1471, 'throughput_ok': True, 'tile_count': 786, 'vocab_size': 50257}` |
| prior_replay_clean_at_selected_cadence | `True` | `{'expected_throughput_ok': True, 'lanes_per_cycle': 1, 'producer_ii_cycles': 384, 'ranker_service_cycles': 65, 'rtl_sim': {'expected': {'logit': 500, 'token': 5}, 'log_tail': ['RESULT scenario=ii384 lpc=1 producer_ii=384 token=5 logit=500 accepted=6 tb_backpressure=0 dut_stalls=0 fifo_max=1 final_cycle=1987', '/tmp/tmppauchxzu/tb_decoder_r64_k1_serial_rank_lpc1_wrapper_producer_replay_ii384.v:505: $finish called at 19910000 (1ps)'], 'observed': {'accepted': 6, 'dut_stalls': 0, 'fifo_max': 1, 'final_cycle': 1987, 'logit': 500, 'lpc': 1, 'producer_ii': 384, 'scenario': 'ii384', 'tb_backpressure': 0, 'token': 5}, 'returncode': 0, 'status': 'ok'}, 'scenario': 'ii384'}` |
| focused_rtl_replay_matches_reference | `True` | `{'status': 'ok', 'returncode': 0, 'expected': {'token': 5, 'logit': 500}, 'log_tail': ['RESULT scenario=selected_ii384 lpc=1 producer_ii=384 token=5 logit=500 accepted=6 tb_backpressure=0 dut_stalls=0 fifo_max=1 final_cycle=1987', '/tmp/tmpxc0eidc2/tb_decoder_r64_k1_serial_rank_lpc1_wrapper_producer_replay_selected_ii384.v:505: $finish called at 19910000 (1ps)'], 'observed': {'scenario': 'selected_ii384', 'lpc': 1, 'producer_ii': 384, 'token': 5, 'logit': 500, 'accepted': 6, 'tb_backpressure': 0, 'dut_stalls': 0, 'fifo_max': 1, 'final_cycle': 1987}}` |

## Assumptions

- The promoted wrapper is the measured serial_lpc1 ranker plus candidate merge FIFO, not a synthetic producer ROM.
- The output-projection producer is assumed to issue r64 tiles no faster than the selected 384-cycle cadence.
- The focused replay validates ready-valid behavior at the selected cadence and carries prior PPA from the serial architecture sweep.
- If a resident-weight or cached producer issues faster tiles, lpc2/lpc4 remain guard candidates from the replay result.
