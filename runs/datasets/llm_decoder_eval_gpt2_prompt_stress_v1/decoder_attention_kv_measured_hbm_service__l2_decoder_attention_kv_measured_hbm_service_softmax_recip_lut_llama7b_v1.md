# Llama7B Measured-HBM Service Closure

- source rows used: `16`
- generated rows: `139968`
- dominant resources: `{'hbm': 97184, 'tile_attention': 42784}`

## Best

| latency us | resource | hbm share | eff B/cyc | source eff B/cyc | eff/source | channels | ch B/cyc | burst | outstanding | row hit | sched eff | service cycles |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2138.84136 | tile_attention | 0.983398438 | 792.596465 | 41341.3632 | 0.019172 | 4 | 256.0 | 512 | 32 | 0.9 | 0.9 | 1301 |

## Top Rows

| rank | latency us | resource | eff/source | channels | ch B/cyc | burst | outstanding | row hit | sched eff |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2138.84136 | tile_attention | 0.019172 | 4 | 256.0 | 512 | 32 | 0.9 | 0.9 |
| 2 | 2138.84136 | tile_attention | 0.019172 | 4 | 256.0 | 1024 | 16 | 0.9 | 0.9 |
| 3 | 2138.84136 | tile_attention | 0.019026 | 4 | 256.0 | 1024 | 32 | 0.5 | 0.9 |
| 4 | 2138.84136 | tile_attention | 0.020002 | 4 | 256.0 | 1024 | 32 | 0.75 | 0.9 |
| 5 | 2138.84136 | tile_attention | 0.019026 | 4 | 256.0 | 1024 | 32 | 0.75 | 0.9 |
| 6 | 2138.84136 | tile_attention | 0.020529 | 4 | 256.0 | 1024 | 32 | 0.9 | 0.9 |
| 7 | 2138.84136 | tile_attention | 0.020002 | 4 | 256.0 | 1024 | 32 | 0.9 | 0.9 |
| 8 | 2138.84136 | tile_attention | 0.019026 | 4 | 256.0 | 1024 | 32 | 0.9 | 0.9 |
| 9 | 2138.84136 | tile_attention | 0.019026 | 4 | 256.0 | 1024 | 32 | 0.75 | 0.9 |
| 10 | 2138.84136 | tile_attention | 0.019502 | 4 | 256.0 | 1024 | 32 | 0.9 | 0.9 |
| 11 | 2138.84136 | tile_attention | 0.019026 | 4 | 256.0 | 1024 | 32 | 0.9 | 0.9 |
| 12 | 2138.84136 | tile_attention | 0.019609 | 4 | 512.0 | 256 | 16 | 0.9 | 0.9 |
| 13 | 2138.84136 | tile_attention | 0.018953 | 4 | 512.0 | 256 | 32 | 0.5 | 0.9 |
| 14 | 2138.84136 | tile_attention | 0.018504 | 4 | 512.0 | 256 | 32 | 0.75 | 0.6 |
| 15 | 2138.84136 | tile_attention | 0.021138 | 4 | 512.0 | 256 | 32 | 0.75 | 0.75 |
| 16 | 2138.84136 | tile_attention | 0.023355 | 4 | 512.0 | 256 | 32 | 0.75 | 0.9 |
| 17 | 2138.84136 | tile_attention | 0.018839 | 4 | 512.0 | 256 | 32 | 0.75 | 0.9 |
| 18 | 2138.84136 | tile_attention | 0.020855 | 4 | 512.0 | 256 | 32 | 0.9 | 0.6 |
| 19 | 2138.84136 | tile_attention | 0.024263 | 4 | 512.0 | 256 | 32 | 0.9 | 0.75 |
| 20 | 2138.84136 | tile_attention | 0.02723 | 4 | 512.0 | 256 | 32 | 0.9 | 0.9 |
| 21 | 2138.84136 | tile_attention | 0.019187 | 4 | 512.0 | 256 | 32 | 0.9 | 0.6 |
| 22 | 2138.84136 | tile_attention | 0.022034 | 4 | 512.0 | 256 | 32 | 0.9 | 0.75 |
| 23 | 2138.84136 | tile_attention | 0.024454 | 4 | 512.0 | 256 | 32 | 0.9 | 0.9 |
| 24 | 2138.84136 | tile_attention | 0.018614 | 4 | 512.0 | 256 | 32 | 0.9 | 0.75 |
| 25 | 2138.84136 | tile_attention | 0.020312 | 4 | 512.0 | 256 | 32 | 0.9 | 0.9 |
| 26 | 2138.84136 | tile_attention | 0.018896 | 4 | 512.0 | 256 | 32 | 0.75 | 0.9 |
| 27 | 2138.84136 | tile_attention | 0.019487 | 4 | 512.0 | 256 | 32 | 0.9 | 0.75 |
| 28 | 2138.84136 | tile_attention | 0.021355 | 4 | 512.0 | 256 | 32 | 0.9 | 0.9 |
| 29 | 2138.84136 | tile_attention | 0.019609 | 4 | 512.0 | 256 | 32 | 0.9 | 0.9 |
| 30 | 2138.84136 | tile_attention | 0.019609 | 4 | 512.0 | 512 | 8 | 0.9 | 0.9 |

## Assumptions

- Payload cycles are bounded by channel_count * channel_bandwidth_bytes_per_cycle * scheduler_efficiency.
- Burst command overhead and row-miss penalties are batched by the outstanding-request window.
- The model refines HBM service on top of the measured-SRAM rebalance frontier; compute, SRAM, endpoint, and NoC parameters are inherited.
- This is an analytic HBM service bound, not a full DRAM timing simulator with bank groups, refresh, turnarounds, or address mapping.
