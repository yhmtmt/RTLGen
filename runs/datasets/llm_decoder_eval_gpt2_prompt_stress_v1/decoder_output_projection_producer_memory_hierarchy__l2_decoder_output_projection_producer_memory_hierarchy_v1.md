# Decoder Output-Projection Producer Memory Hierarchy

- model: `decoder_output_projection_producer_memory_hierarchy_v1`
- decision: `producer_memory_hierarchy_estimated`
- row_count: `4050`

## Shape Summary

| shape | seq | baseline_us | best_parallel_us | parallel_speedup | best_serial_us | serial_speedup | resident_weight_mb | best_cache_mb | best_hit | best_limiter |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt2_medium_proxy | 128 | 401.42 | 5.687 | 70.585546 | 6.274 | 63.981511 | 98.5 | 128.0 | 0.9 | weight_memory |
| gpt2_small | 128 | 301.065 | 4.314 | 69.7879 | 4.706 | 63.974713 | 73.6875 | 128.0 | 0.9 | weight_memory |

## Assumptions

- This is an analytical producer service model; it does not include a routed SRAM/cache macro.
- Cache capacity constrains the effective weight hit rate by resident bytes divided by output-projection weight bytes.
- Parallel latency assumes local-cache hits and off-chip misses are served by independent paths; serial latency sums them conservatively.
- Hidden vector load is still charged once from off-chip memory.
- Ranker latency is excluded because the calibrated frontier showed measured r64/r128 ranker service is not dominant.
