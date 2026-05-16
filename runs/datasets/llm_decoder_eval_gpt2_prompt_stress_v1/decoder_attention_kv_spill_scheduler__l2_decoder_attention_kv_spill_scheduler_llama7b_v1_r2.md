# Decoder Attention/KV Spill Scheduler

- model: `llm_decoder_attention_kv_spill_scheduler_llama7b_131k_v1`
- generated_row_count: `5400`
- selected_point: `llama7b_proxy seq=131072 die=400.0mm2`

## Best

| tile | prefetch_dist | hbm_out | hbm_eff | arb_eff | vc | start | latency_us | layer_cycles | tile_resource | hbm_share | hbm_stall | shared_stall |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|
| 2048 | 2 | 2 | 0.6 | 0.85 | 4 | during_qkv | 77.92 | 2435 | hbm | 0.266583 | 23 | 32 |

## Top 10

| rank | tile | prefetch_dist | hbm_out | hbm_eff | arb_eff | vc | start | latency_us | resource |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | 2048 | 2 | 2 | 0.6 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 2 | 2048 | 2 | 2 | 0.8 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 3 | 2048 | 2 | 4 | 0.6 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 4 | 2048 | 2 | 4 | 0.8 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 5 | 2048 | 2 | 8 | 0.6 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 6 | 2048 | 2 | 8 | 0.8 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 7 | 2048 | 4 | 2 | 0.6 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 8 | 2048 | 4 | 2 | 0.8 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 9 | 2048 | 4 | 4 | 0.6 | 0.85 | 4 | during_qkv | 77.92 | hbm |
| 10 | 2048 | 4 | 4 | 0.8 | 0.85 | 4 | during_qkv | 77.92 | hbm |

## Assumptions

- This is a tile-level spill scheduler estimator for the selected llama7b_proxy 131k 400 mm2 point.
- The KV cache residency split is inherited from the capacity/NoC best_by_die result.
- HBM traffic may be prefetched during or after QKV production, with finite outstanding requests and a finite prefetch window.
- Shared-SRAM traffic is serialized through a compact bank plus NoC path model with hop latency, arbitration efficiency, virtual-channel relief, and bank conflict efficiency.
- Tile attention compute waits for both shared-resident and HBM-spilled KV bytes for that tile; tile compute itself is serialized.
- This is still a scheduler model, not RTL NoC arbitration or SRAM macro timing.
