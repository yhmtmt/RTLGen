# Decoder Attention/KV Physical HBM Frontier

- model: `llm_decoder_attention_kv_physical_hbm_frontier_llama7b_v1`
- generated_row_count: `5184`
- selected_point: `llama7b_proxy seq=32768 die=100.0mm2`

## Best

| seq | die | kv | bits | MAC/cyc | vec/cyc | stacks | pch/stack | width | MT/s | eff | hbm_B/cyc | hbm_share | latency_us | resource |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 32768 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 64 | 9000 | 0.75 | 6912.0 | 0.816646 | 30.944 | hbm |

## Best By Sequence And Die

| seq | die | kv | bits | MAC/cyc | vec/cyc | stacks | MT/s | SRAM MiB | local_frac | NoC B/cyc | hops | hbm_share | latency_us | resource |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 32768 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 9000 | 250.339508 | 0.25 | 16384.0 | 1 | 0.816646 | 30.944 | hbm |
| 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 6400 | 500.679016 | 0.25 | 16384.0 | 1 | 0.633292 | 34.4 | hbm |
| 32768 | 400.0 | gqa8 | 16 | 524288 | 65536 | 8 | 6400 | 1001.358032 | 0.25 | 16384.0 | 1 | 0.633292 | 66.432 | hbm |
| 65536 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 9000 | 250.339508 | 0.25 | 16384.0 | 1 | 0.908323 | 66.4 | hbm |
| 65536 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 9000 | 500.679016 | 0.25 | 16384.0 | 1 | 0.816646 | 60.576 | hbm |
| 65536 | 400.0 | gqa8 | 8 | 524288 | 65536 | 8 | 6400 | 1001.358032 | 0.25 | 16384.0 | 1 | 0.633292 | 67.168 | hbm |
| 131072 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 9000 | 250.339508 | 0.25 | 16384.0 | 1 | 0.954161 | 137.696 | hbm |
| 131072 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 9000 | 500.679016 | 0.25 | 16384.0 | 1 | 0.908323 | 131.488 | hbm |
| 131072 | 400.0 | gqa8 | 8 | 524288 | 65536 | 8 | 9000 | 1001.358032 | 0.25 | 16384.0 | 1 | 0.816646 | 119.84 | hbm |

## Top 10

| rank | seq | die | kv | bits | MAC/cyc | vec/cyc | stacks | pch/stack | MT/s | hbm_B/cyc | hbm_share | latency_us | resource |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 32768 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 6912.0 | 0.816646 | 30.944 | hbm |
| 2 | 32768 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 6912.0 | 0.816646 | 30.944 | hbm |
| 3 | 32768 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 6912.0 | 0.816646 | 32.672 | hbm |
| 4 | 32768 | 100.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 6912.0 | 0.816646 | 32.672 | hbm |
| 5 | 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 6400 | 4915.2 | 0.633292 | 34.4 | hbm |
| 6 | 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 6400 | 4915.2 | 0.633292 | 34.4 | hbm |
| 7 | 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 5068.8 | 0.633292 | 34.4 | hbm |
| 8 | 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 5068.8 | 0.633292 | 34.4 | hbm |
| 9 | 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 6912.0 | 0.633292 | 34.4 | hbm |
| 10 | 32768 | 200.0 | gqa8 | 8 | 524288 | 65536 | 8 | 16 | 9000 | 6912.0 | 0.633292 | 34.4 | hbm |

## Assumptions

- This is a planning model for single-token decode attention/KV, not a JEDEC HBM timing model.
- HBM bandwidth is derived from stack count, pseudo-channel count, interface width, MT/s, and the core clock period.
- HBM efficiency represents controller scheduling, protocol overhead, row locality, and clock-crossing loss in aggregate.
- KV bits are treated as packed storage bits, so kv4 has half the byte traffic of kv8.
- Shared SRAM residency is capacity-based; the remaining KV-cache traffic spills to HBM.
- MAC/cycle and vector-op/cycle values are throughput proxies for architecture sizing, not physical proofs of an implemented array.
- The tile scheduler is a compact service model intended to rank architecture directions before RTL.

## Native KV Quality Gate Summary

- status: `native_checkpoint_kv4_promising`
- model: `mistralai/Mistral-7B-v0.1`
- gqa_group_size: `4.0`

## Cautions

- Best KV4 ranking mostly holds, but logit cosine is below the promotion caution line

### KV8 summary

| bits | granularity | top1 | top-k | cosine | kl | comparisons | margin | delta |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8 | tensor | 1.0 | 1.0 | 0.9999542478621327 | 0.0004798215588894854 | 8 | 0.0 | 0.4375 |

### KV4 summary

| bits | granularity | top1 | top-k | cosine | kl | comparisons | margin | delta |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 4 | tensor | 1.0 | 1.0 | 0.9978199414249704 | 0.01678496644161117 | 8 | 0.0 | 2.3125 |

### best KV4 candidate

- granularity: `tensor`
- top1_match_rate: `1.0`
- topk_contains_rate: `1.0`
- mean_logit_cosine: `0.9978199414249704`
