# Decoder Output-Projection Cadence Sensitivity

- model: `decoder_output_projection_cadence_sensitivity_v1`
- decision: `resident_weight_can_outpace_serial_ranker`
- serial_safe_rows: `96/128`
- next_step: Measure or model producer output cadence under resident/cache-backed output weights. If cadence approaches the unsafe rows, evaluate a buffered or rank-tree producer-coupled wrapper.

## Ranker Thresholds

| ranker | min zero-backpressure II | service cycles |
|---|---:|---:|
| serial_lpc1 | 384 | 65 |
| serial_lpc2 | 65 | 33 |
| serial_lpc4 | 33 | 17 |

## Cadence Sweep

| vocab | hidden | W | MAC/cycle | BW | hit | prod II | limiter | selected ranker | decision |
|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 50257 | 768 | 64 | 8192 | 64.0 | 0.0 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 64 | 8192 | 64.0 | 0.5 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 64 | 8192 | 64.0 | 0.9 | 154 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 64 | 8192 | 64.0 | 1.0 | 6 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 64 | 8192 | 256.0 | 0.0 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 64 | 8192 | 256.0 | 0.5 | 192 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 64 | 8192 | 256.0 | 0.9 | 39 | weight_memory | serial_lpc4 | serial_ranker_safe |
| 50257 | 768 | 64 | 8192 | 256.0 | 1.0 | 6 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 64 | 32768 | 64.0 | 0.0 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 64 | 32768 | 64.0 | 0.5 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 64 | 32768 | 64.0 | 0.9 | 154 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 64 | 32768 | 64.0 | 1.0 | 2 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 64 | 32768 | 256.0 | 0.0 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 64 | 32768 | 256.0 | 0.5 | 192 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 64 | 32768 | 256.0 | 0.9 | 39 | weight_memory | serial_lpc4 | serial_ranker_safe |
| 50257 | 768 | 64 | 32768 | 256.0 | 1.0 | 2 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 128 | 8192 | 64.0 | 0.0 | 3072 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 8192 | 64.0 | 0.5 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 8192 | 64.0 | 0.9 | 308 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 128 | 8192 | 64.0 | 1.0 | 12 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 128 | 8192 | 256.0 | 0.0 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 8192 | 256.0 | 0.5 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 8192 | 256.0 | 0.9 | 77 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 128 | 8192 | 256.0 | 1.0 | 12 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 128 | 32768 | 64.0 | 0.0 | 3072 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 32768 | 64.0 | 0.5 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 32768 | 64.0 | 0.9 | 308 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 128 | 32768 | 64.0 | 1.0 | 3 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 768 | 128 | 32768 | 256.0 | 0.0 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 32768 | 256.0 | 0.5 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 768 | 128 | 32768 | 256.0 | 0.9 | 77 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 768 | 128 | 32768 | 256.0 | 1.0 | 3 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 64 | 8192 | 64.0 | 0.0 | 4096 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 8192 | 64.0 | 0.5 | 2048 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 8192 | 64.0 | 0.9 | 410 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 8192 | 64.0 | 1.0 | 16 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 64 | 8192 | 256.0 | 0.0 | 1024 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 8192 | 256.0 | 0.5 | 512 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 8192 | 256.0 | 0.9 | 103 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 2048 | 64 | 8192 | 256.0 | 1.0 | 16 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 64 | 32768 | 64.0 | 0.0 | 4096 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 32768 | 64.0 | 0.5 | 2048 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 32768 | 64.0 | 0.9 | 410 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 32768 | 64.0 | 1.0 | 4 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 64 | 32768 | 256.0 | 0.0 | 1024 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 32768 | 256.0 | 0.5 | 512 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 64 | 32768 | 256.0 | 0.9 | 103 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 2048 | 64 | 32768 | 256.0 | 1.0 | 4 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 128 | 8192 | 64.0 | 0.0 | 8192 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 8192 | 64.0 | 0.5 | 4096 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 8192 | 64.0 | 0.9 | 820 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 8192 | 64.0 | 1.0 | 32 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 128 | 8192 | 256.0 | 0.0 | 2048 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 8192 | 256.0 | 0.5 | 1024 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 8192 | 256.0 | 0.9 | 205 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 2048 | 128 | 8192 | 256.0 | 1.0 | 32 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 128 | 32768 | 64.0 | 0.0 | 8192 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 32768 | 64.0 | 0.5 | 4096 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 32768 | 64.0 | 0.9 | 820 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 32768 | 64.0 | 1.0 | 8 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 50257 | 2048 | 128 | 32768 | 256.0 | 0.0 | 2048 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 32768 | 256.0 | 0.5 | 1024 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 50257 | 2048 | 128 | 32768 | 256.0 | 0.9 | 205 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 50257 | 2048 | 128 | 32768 | 256.0 | 1.0 | 8 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 64 | 8192 | 64.0 | 0.0 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 64 | 8192 | 64.0 | 0.5 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 64 | 8192 | 64.0 | 0.9 | 154 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 64 | 8192 | 64.0 | 1.0 | 6 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 64 | 8192 | 256.0 | 0.0 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 64 | 8192 | 256.0 | 0.5 | 192 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 64 | 8192 | 256.0 | 0.9 | 39 | weight_memory | serial_lpc4 | serial_ranker_safe |
| 100000 | 768 | 64 | 8192 | 256.0 | 1.0 | 6 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 64 | 32768 | 64.0 | 0.0 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 64 | 32768 | 64.0 | 0.5 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 64 | 32768 | 64.0 | 0.9 | 154 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 64 | 32768 | 64.0 | 1.0 | 2 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 64 | 32768 | 256.0 | 0.0 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 64 | 32768 | 256.0 | 0.5 | 192 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 64 | 32768 | 256.0 | 0.9 | 39 | weight_memory | serial_lpc4 | serial_ranker_safe |
| 100000 | 768 | 64 | 32768 | 256.0 | 1.0 | 2 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 128 | 8192 | 64.0 | 0.0 | 3072 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 8192 | 64.0 | 0.5 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 8192 | 64.0 | 0.9 | 308 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 128 | 8192 | 64.0 | 1.0 | 12 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 128 | 8192 | 256.0 | 0.0 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 8192 | 256.0 | 0.5 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 8192 | 256.0 | 0.9 | 77 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 128 | 8192 | 256.0 | 1.0 | 12 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 128 | 32768 | 64.0 | 0.0 | 3072 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 32768 | 64.0 | 0.5 | 1536 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 32768 | 64.0 | 0.9 | 308 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 128 | 32768 | 64.0 | 1.0 | 3 | compute_array | None | serial_ranker_not_safe_at_this_cadence |
| 100000 | 768 | 128 | 32768 | 256.0 | 0.0 | 768 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 32768 | 256.0 | 0.5 | 384 | weight_memory | serial_lpc1 | serial_ranker_safe |
| 100000 | 768 | 128 | 32768 | 256.0 | 0.9 | 77 | weight_memory | serial_lpc2 | serial_ranker_safe |
| 100000 | 768 | 128 | 32768 | 256.0 | 1.0 | 3 | compute_array | None | serial_ranker_not_safe_at_this_cadence |

## Assumptions

- weight_cache_hit_rate reduces output-projection weight bytes charged per tile; 1.0 is a resident-weight bound.
- compute_cycles_per_tile still charges producer_lanes * hidden_size MACs per tile.
- Ranker safety uses replay-observed zero-backpressure thresholds, not only analytical service cycles.
- The model does not add buffering between producer and ranker; buffering could absorb bursty faster producer rows.
