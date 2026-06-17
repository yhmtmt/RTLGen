# Llama7B Sub-Tile Pipelined Attention Schedule

- source rows used: `2`
- generated rows: `18432`
- legal rows: `6528`
- dominant resources: `{'pipeline_attention': 6528}`

## Best

| latency us | speedup | tile service | resource | mode | normalize | subtiles | buffers | prefetch | softmax/sub | rescale | area mult | hbm gap | req buffer |
|---:|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1575.373891 | 1.357672 | 986 | pipeline_attention | dual_mac | online_correction | 8 | 4 | 3 | 0 | 0 | 2.0 | -315 | 532608 |

## Best By Compute Mode

| mode | latency us | speedup | tile service | resource | normalize | subtiles | area mult | hbm gap |
|---|---:|---:|---:|---|---|---:|---:|---:|
| dual_mac | 1575.373891 | 1.357672 | 986 | pipeline_attention | online_correction | 8 | 2.0 | -315 |
| split_mac | 2042.378179 | 1.047231 | 1291 | pipeline_attention | online_correction | 32 | 1.0 | -10 |
| shared_mac | 2141.903683 | 0.99857 | 1356 | pipeline_attention | online_correction | 4 | 1.0 | 55 |

## Best By Normalize Strategy

| normalize | mode | latency us | speedup | tile service | subtiles | softmax/sub | rescale |
|---|---|---:|---:|---:|---:|---:|---:|
| online_correction | dual_mac | 1575.373891 | 1.357672 | 986 | 8 | 0 | 0 |
| online_correction | split_mac | 2042.378179 | 1.047231 | 1291 | 32 | 0 | 0 |
| online_correction | shared_mac | 2141.903683 | 0.99857 | 1356 | 4 | 0 | 0 |
| full_tile_normalize | shared_mac | 2411.388125 | 0.886975 | 1532 | 8 | 0 | 0 |
| full_tile_normalize | dual_mac | 2411.388125 | 0.886975 | 1532 | 8 | 0 | 0 |
| full_tile_normalize | split_mac | 3885.896746 | 0.550411 | 2495 | 8 | 0 | 0 |

## Assumptions

- The source row is the measured-SRAM, measured-HBM, HBM-closed on-chip schedule frontier.
- shared_mac keeps QK and V on one measured MAC resource; split_mac partitions the same resource; dual_mac models independent QK and V streams and therefore carries a compute_area_multiplier of 2.
- full_tile_normalize requires all subtile stats before V starts; online_correction allows V to stream after each subtile stats result with an explicit rescale penalty.
- A row is legal only if the required stream buffer fits local capacity and prefetch_distance is less than the available subtile buffer count.
- This is a scheduling feasibility model, not RTL or PPA for the pipelined datapath.
