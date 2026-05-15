# Decoder Attention/KV Capacity + NoC Baseline

- model: `llm_decoder_attention_kv_capacity_noc_baseline_v1`
- generated_row_count: `12597120`
- feasible_row_count: `6544152`

## Best By Die

| shape | seq | die_mm2 | placement | share | bits | latency_us | kv_MiB | total_sram_MiB | local_MiB | shared_MiB | limiter | noc_hops | noc_B/cyc | bank_count | bank_B/cyc |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| gpt2_medium_proxy | 32768 | 25.0 | shared_sram_hbm_spill | mqa | 8 | 16.579 | 96.0 | 62.584877 | 15.646219 | 46.938658 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_medium_proxy | 32768 | 50.0 | shared_sram_hbm_spill | mqa | 8 | 7.567 | 96.0 | 125.169754 | 31.292439 | 93.877316 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_medium_proxy | 32768 | 100.0 | local_sram | mqa | 8 | 4.086 | 96.0 | 131.130219 | 98.347664 | 32.782555 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_medium_proxy | 32768 | 200.0 | local_sram | mqa | 8 | 4.086 | 96.0 | 131.130219 | 98.347664 | 32.782555 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_medium_proxy | 32768 | 400.0 | local_sram | mqa | 8 | 4.086 | 96.0 | 262.260437 | 131.130219 | 131.130219 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_medium_proxy | 131072 | 25.0 | shared_sram_hbm_spill | mqa | 8 | 93.187 | 384.0 | 62.584877 | 15.646219 | 46.938658 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_medium_proxy | 131072 | 50.0 | shared_sram_hbm_spill | mqa | 8 | 84.175 | 384.0 | 125.169754 | 31.292439 | 93.877316 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_medium_proxy | 131072 | 100.0 | shared_sram_hbm_spill | mqa | 8 | 66.15 | 384.0 | 250.339508 | 62.584877 | 187.754631 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_medium_proxy | 131072 | 200.0 | shared_sram_hbm_spill | mqa | 8 | 30.101 | 384.0 | 500.679016 | 125.169754 | 375.509262 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_medium_proxy | 131072 | 400.0 | local_sram | mqa | 8 | 16.182 | 384.0 | 524.520874 | 393.390656 | 131.130219 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_small | 32768 | 25.0 | shared_sram_hbm_spill | mqa | 8 | 3.653 | 48.0 | 62.584877 | 15.646219 | 46.938658 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_small | 32768 | 50.0 | local_sram | mqa | 8 | 1.528 | 48.0 | 65.565109 | 49.173832 | 16.391277 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_small | 32768 | 100.0 | local_sram | mqa | 8 | 1.528 | 48.0 | 65.565109 | 49.173832 | 16.391277 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_small | 32768 | 200.0 | local_sram | mqa | 8 | 1.528 | 48.0 | 131.130219 | 65.565109 | 65.565109 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_small | 32768 | 400.0 | local_sram | mqa | 8 | 1.528 | 48.0 | 262.260437 | 65.565109 | 196.695328 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_small | 131072 | 25.0 | shared_sram_hbm_spill | mqa | 8 | 41.597 | 192.0 | 62.584877 | 15.646219 | 46.938658 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_small | 131072 | 50.0 | shared_sram_hbm_spill | mqa | 8 | 32.585 | 192.0 | 125.169754 | 31.292439 | 93.877316 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_small | 131072 | 100.0 | shared_sram_hbm_spill | mqa | 8 | 14.56 | 192.0 | 250.339508 | 62.584877 | 187.754631 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| gpt2_small | 131072 | 200.0 | local_sram | mqa | 8 | 6.064 | 192.0 | 262.260437 | 196.695328 | 65.565109 | compute | 1 | 1024.0 | 64 | 1024.0 |
| gpt2_small | 131072 | 400.0 | local_sram | mqa | 8 | 6.064 | 192.0 | 262.260437 | 196.695328 | 65.565109 | compute | 1 | 1024.0 | 64 | 1024.0 |
| llama7b_proxy | 32768 | 25.0 | shared_sram_hbm_spill | mqa | 8 | 60.173 | 256.0 | 62.584877 | 15.646219 | 46.938658 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 32768 | 50.0 | shared_sram_hbm_spill | mqa | 8 | 51.161 | 256.0 | 125.169754 | 31.292439 | 93.877316 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 32768 | 100.0 | shared_sram_hbm_spill | mqa | 8 | 33.136 | 256.0 | 250.339508 | 62.584877 | 187.754631 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 32768 | 200.0 | local_sram | mqa | 8 | 20.032 | 256.0 | 393.390656 | 295.042992 | 98.347664 | compute | 1 | 1024.0 | 64 | 1024.0 |
| llama7b_proxy | 32768 | 400.0 | local_sram | mqa | 8 | 20.032 | 256.0 | 524.520874 | 262.260437 | 262.260437 | compute | 1 | 1024.0 | 64 | 1024.0 |
| llama7b_proxy | 131072 | 25.0 | shared_sram_hbm_spill | mqa | 8 | 264.461 | 1024.0 | 62.584877 | 15.646219 | 46.938658 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 131072 | 50.0 | shared_sram_hbm_spill | mqa | 8 | 255.449 | 1024.0 | 125.169754 | 31.292439 | 93.877316 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 131072 | 100.0 | shared_sram_hbm_spill | mqa | 8 | 237.424 | 1024.0 | 250.339508 | 62.584877 | 187.754631 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 131072 | 200.0 | shared_sram_hbm_spill | mqa | 8 | 201.376 | 1024.0 | 500.679016 | 125.169754 | 375.509262 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |
| llama7b_proxy | 131072 | 400.0 | shared_sram_hbm_spill | mqa | 8 | 129.278 | 1024.0 | 1001.358032 | 250.339508 | 751.018524 | hbm_bw | 1 | 16384.0 | 16 | 1024.0 |

## Assumptions

- This is a capacity/bandwidth baseline, not a cycle-accurate NoC scheduler.
- Local SRAM and shared SRAM placements are disallowed unless the full KV cache fits in the selected capacity.
- The shared_sram_hbm_spill placement reads the resident fraction from shared SRAM and the remainder from HBM.
- NoC bandwidth is approximated as bisection bandwidth divided by hop count for shared SRAM traffic.
- Bank conflicts, packet arbitration, routing, replacement, ECC, and SRAM macro timing are not modeled.
