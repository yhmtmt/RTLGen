# Decoder Frontier Synthesis

- model: `llm_decoder_frontier_synthesis_v1`

## Focus Summary

| shape | seq | dominant | share | attention_us | mlp_us | producer_ranker_us | attention choice | producer choice |
|---|---:|---|---:|---:|---:|---:|---|---|
| gpt2_medium_proxy | 128 | output_projection_producer_ranker | 0.998767 | 1.392 | 6.144 | 6728.322951 | local_sram/mqa/kv8/hops0 | w64/k1/share1.0/ii512 |
| gpt2_small | 128 | output_projection_producer_ranker | 0.999491 | 0.552 | 1.728 | 5046.275694 | local_sram/mqa/kv8/hops0 | w64/k1/share1.0/ii384 |

## Measured Attention/KV Tile Summary

- area_growth_largest_vs_smallest: `23.809901`
- fastest_critical_path_ns: `4.4824`
- fastest_design: `attention_kv_tile_hd64_kv4_l16_b128_wrapper`
- largest_design: `attention_kv_tile_hd128_kv16_l64_b512_wrapper`
- largest_die_area_um2: `269044.503025`
- smallest_design: `attention_kv_tile_hd64_kv4_l16_b128_wrapper`
- smallest_die_area_um2: `11299.69`

## Producer Control Boundary

- decision: `softmax_event_guard_synth_ok_under_bound`
- guard_variant: `cq_v1_softmax_event_guard`
- synthesis_status: `ok`
- synthesis_elapsed_seconds: `196.19542427099077`
- reg_bits_est: `2634`
- wire_bits_est: `3864`

## Producer Physical Boundary

- decision: `producer_physical_boundary_not_reached`
- make_target: `3_3_place_gp`
- num_modules: `16`
- critical_path_ns: `6.10444708970485`
- die_area_um2: `4840000.0`
- total_power_mw: `0.254279`
- synthesis_elapsed_seconds: `822.8356093889743`
- result_path: `runs/designs/npu_blocks/npu_fp16_cpp_nm16_producer/work/3a2fb3e1/result.json`

## Producer/Ranker Integration Accounting

- decision: `producer_output_ranker_integration_accounting_passed`
- ok_integrations: `4`
- total_integrations: `4`
- max_ranker_area_over_producer: `0.123332`
- max_ranker_power_over_producer: `0.14483589494995577`

| arch | macro | lanes | bottleneck | cp ns |
|---|---|---:|---|---:|
| fp16_nm1 | flat_nomacro | 64 | producer | 5.557037432204143 |
| fp16_nm1 | hier_macro | 64 | producer | 5.774905724664045 |
| fp16_nm2 | flat_nomacro | 128 | producer | 5.701286780426342 |
| fp16_nm2 | hier_macro | 128 | producer | 5.740890641774165 |

## Assumptions

- This is a synthesis of existing analytical reports, not a new RTL measurement.
- Attention/KV uses the best latency row per shape and sequence from the calibrated attention/KV report.
- Producer/ranker uses the best FIFO-valid coupled row per hidden/vocab shape.
- Producer physical-boundary evidence is carried as feasibility/PPA context; it does not replace the analytical producer/ranker latency model.
- Producer/ranker integration accounting is carried as measured additive PPA context; it does not replace the analytical coupled latency model.
- MLP and norm are resident-weight estimates from the whole-decoder stage breakdown.
- Use this report to choose the next measured RTL frontier, not as final PPA accounting.
