# Decoder Attention/KV Selected NoC Scheduler

- model: `llm_decoder_attention_kv_noc_scheduler_selected_v1`
- selected_point_count: `5`
- generated_row_count: `225`

## Best By Point

| shape | seq | die_mm2 | placement | tile | vc | arb_eff | strict_us | overlap_us | gain | limiter | noc_cyc/layer | mem_parallel/layer |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| gpt2_medium_proxy | 131072 | 200.0 | shared_sram_hbm_spill | 2048 | 4 | 0.85 | 38.16 | 35.904 | 1.062834 | memory_parallel | 1307 | 1336 |
| gpt2_medium_proxy | 131072 | 400.0 | local_sram | 1024 | 1 | 0.55 | 16.2 | 16.128 | 1.004464 | qk_value_compute | 0 | 342 |
| gpt2_small | 131072 | 100.0 | shared_sram_hbm_spill | 2048 | 4 | 0.85 | 18.588 | 17.472 | 1.063874 | memory_parallel | 1307 | 1336 |
| gpt2_small | 131072 | 200.0 | local_sram | 1024 | 1 | 0.55 | 6.072 | 6.048 | 1.003968 | qk_value_compute | 0 | 342 |
| llama7b_proxy | 131072 | 400.0 | shared_sram_hbm_spill | 1024 | 4 | 0.85 | 145.984 | 80.128 | 1.821885 | memory_parallel | 2024 | 2184 |

## Assumptions

- This is a selected-point scheduler estimator, not a cycle-accurate RTL NoC simulation.
- Selected points come from the capacity-constrained best_by_die frontier.
- Strict latency serializes producer, memory resources, and compute; overlap latency is a lower-bound schedule where independent producer, compute, local SRAM, shared SRAM/NoC, and HBM resources can run concurrently.
- NoC scheduling accounts for hop latency, arbitration efficiency, virtual-channel throughput relief, and payload bandwidth divided by hop count.
- SRAM bank pressure uses tile size, bank interleave granularity, selected bank count, and a bank conflict efficiency.
- Producer overlap here means QKV/KV-write service overlap within the selected attention/KV datapath; inter-layer transformer dependencies are not removed.
