# Decoder Attention/KV HBM Controller Realism

- model: `llm_decoder_attention_kv_hbm_controller_llama7b_131k_v1`
- generated_row_count: `419904`
- selected_point: `llama7b_proxy seq=131072 die=400.0mm2`

## Best

| tile | channels | ch_B/cyc | burst | out | row_hit | sched_eff | hbm_eff | latency_us | resource | hbm_service_cyc |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1024 | 16 | 512.0 | 1024 | 16 | 0.9 | 0.9 | 0.042976 | 111.648 | hbm | 397 |

## Top 10

| rank | tile | channels | burst | out | row_hit | sched_eff | hbm_eff | latency_us | resource |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1024 | 16 | 1024 | 16 | 0.9 | 0.9 | 0.042976 | 111.648 | hbm |
| 2 | 1024 | 16 | 1024 | 16 | 0.9 | 0.9 | 0.042976 | 111.648 | hbm |
| 3 | 1024 | 16 | 1024 | 16 | 0.9 | 0.9 | 0.042976 | 111.648 | hbm |
| 4 | 1024 | 16 | 1024 | 16 | 0.9 | 0.9 | 0.042976 | 111.648 | hbm |
| 5 | 1024 | 16 | 1024 | 16 | 0.9 | 0.75 | 0.04276 | 111.904 | hbm |
| 6 | 1024 | 16 | 1024 | 16 | 0.9 | 0.75 | 0.04276 | 111.904 | hbm |
| 7 | 1024 | 16 | 1024 | 16 | 0.9 | 0.75 | 0.04276 | 111.904 | hbm |
| 8 | 1024 | 16 | 1024 | 16 | 0.9 | 0.75 | 0.04276 | 111.904 | hbm |
| 9 | 1024 | 16 | 1024 | 16 | 0.9 | 0.6 | 0.042441 | 112.672 | hbm |
| 10 | 1024 | 16 | 1024 | 16 | 0.9 | 0.6 | 0.042441 | 112.672 | hbm |

## Assumptions

- This is an HBM-controller service model layered onto the llama7B 131k spill scheduler.
- Effective HBM service is derived from channels, per-channel bandwidth, burst size, command overhead, row-hit rate, row-miss penalty, and scheduler efficiency.
- The derived HBM bandwidth replaces the previous scalar HBM efficiency before running the tile-level spill scheduler.
- NoC/shared-SRAM service still uses the compact bank and arbitration model from the spill scheduler.
- This is not a DRAM timing model; it is intended to bound whether the assumed HBM efficiency is physically plausible.
