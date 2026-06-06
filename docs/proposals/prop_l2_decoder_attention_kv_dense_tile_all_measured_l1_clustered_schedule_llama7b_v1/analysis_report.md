# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1`
- `item_id`: `l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1`
- `run_key`: `l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1_run_201267453c414daa`
- `source_commit`: `af5a94ebaf7a7b435c4cf99a328d33d02bdb4e2b`

## Evaluations Consumed
- Dense tile measured compute: `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- Measured all-L1 local cost profile: `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json`
- SRAM profile: `l2_decoder_attention_sram_profile_v1`
- NoC profile: `l2_decoder_attention_noc_profile_v1`

## Result
- generated rows: `4128768`
- skipped area-budget rows: `847872`
- selected compute source: `dense_gemm_tile`
- selected compute arch: `dense_gemm_16x8_k1_p1`
- selected measured L1 profile: `hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10`
- best point: `1200 mm2`, SRAM fraction `0.4`, logic fraction `0.4`, local SRAM fraction `0.1`
- compute replicas: `1035`
- MAC/cycle: `132480`
- clock: `5.9811 ns`
- latency: `1758.156307 us`
- dominant resource: `cross_tile_reduction`

## Die Frontier
| die mm2 | arch | replicas | MAC/cycle | latency us | dominant resource |
|---:|---|---:|---:|---:|---|
| 200 | dense_gemm_16x8_k1_p1 | 172 | 22016 | 10546.449706 | cross_tile_reduction |
| 400 | dense_gemm_16x8_k1_p1 | 344 | 44032 | 5273.511946 | cross_tile_reduction |
| 800 | dense_gemm_16x8_k1_p1 | 689 | 88192 | 2637.234461 | tile_attention |
| 1200 | dense_gemm_16x8_k1_p1 | 1035 | 132480 | 1758.156307 | cross_tile_reduction |

## Interpretation
- The measured dense 16x8 k1 p1 tile remains the selected compute anchor after measured local datapath, softmax, FIFO, and router overhead is charged.
- At the largest evaluated die/logic point, the schedule reaches roughly the prior 131k MAC/cycle compute target.
- Cross-tile reduction is now often the frontier limiter, so the next architectural work should focus on memory/global NoC and reduction scheduling rather than only increasing dense GEMM tile count.

## Caveats
- SRAM capacity/service and global NoC arbitration are still analytic L2 service terms.
- Dense tile replication still assumes composability without a measured global command-distribution fabric.
- Vector throughput remains tied to MAC throughput by `vector_ops_per_mac`; it is not yet separately measured for the dense tile array.

## Recommendation
- decision: `iterate`
- reason: Keep the dense 16x8 k1 p1 tile as the current measured compute anchor, then evaluate detailed SRAM/global NoC and reduction scheduling around the selected frontier candidates.
