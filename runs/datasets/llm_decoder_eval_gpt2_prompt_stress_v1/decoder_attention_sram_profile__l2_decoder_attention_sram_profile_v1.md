# Llama7B Attention SRAM Profile

## Logical Buffers

| buffer | scope | logical bytes | SRAM shape | role |
|---|---|---:|---|---|
| score_tile_buffer | tile-local score buffering before softmax | 32768 | 1 x depth 1024 x width 256 | read_write |
| softmax_weight_buffer | normalized softmax weights consumed by value accumulation | 32768 | 1 x depth 1024 x width 256 | read_write |
| kv_tile_read_buffer | tile-local K and V read staging for the selected KV sharing | 524288 | 1 x depth 16384 x width 256 | read |
| partial_value_buffer | per-head partial value vector before cross-tile reduction | 16384 | 1 x depth 512 x width 256 | read_write |
| result_writeback_buffer | final attention output writeback staging | 8192 | 1 x depth 256 x width 256 | write |
| softmax_stats_buffer | per-head max and sum statistics for stable normalization | 256 | 1 x depth 8 x width 256 | read_write |

## Totals

- logical_buffer_bytes: `614656`
- allocated_sram_bytes: `614656`
- capacity_overhead: `1.0`

## CACTI Summary

- total_area_um2: `2487735.8073090003`
- max_access_time_ns: `1.4124`
- total_read_energy_pj: `374.6457`
- total_write_energy_pj: `572.2861999999999`

## Notes

- This profile measures tile-local buffering only; the full 131k-token KV cache residency remains a higher-level memory-capacity decision.
- SRAM shapes are banked logical targets for CACTI and are not a placed SRAM macro floorplan.
