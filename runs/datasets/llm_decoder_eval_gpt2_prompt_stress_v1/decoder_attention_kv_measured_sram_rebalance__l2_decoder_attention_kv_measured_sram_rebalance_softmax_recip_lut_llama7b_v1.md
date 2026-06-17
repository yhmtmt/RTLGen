# Llama7B Measured-SRAM Rebalanced Endpoint Schedule

- source rows used: `50`
- generated rows: `50`

## Best

| topology | schedule | clusters | link bits | latency us | hbm share | shared MiB | tile local B/cluster | replaced local B/cluster | resource |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| mesh2d | prefetch_overlap | 16 | 2048 | 2138.84136 | 0.983398438 | 68.0 | 614656 | 19140624 | tile_attention |

## Top Rows

| rank | topology | schedule | bank policy | latency us | hbm share | shared MiB | resource |
|---:|---|---|---|---:|---:|---:|---|
| 1 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 2 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 3 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 4 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 5 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 6 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 7 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 8 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 9 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 10 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 11 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 12 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 13 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 14 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 15 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 16 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 17 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 18 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 19 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 20 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 21 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 22 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 23 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 24 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 25 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 26 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 27 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 28 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 29 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |
| 30 | mesh2d | prefetch_overlap | locality_first | 2138.84136 | 0.983398438 | 68.0 | tile_attention |

## Assumptions

- Tile-local SRAM area is taken from the endpoint/router/SRAM composition audit.
- The remaining SRAM area budget is packed into shared SRAM using the CACTI macro chunks from the local-capacity profile.
- The abstract per-cluster local-capacity pool is replaced by measured tile-local buffer capacity.
- HBM/DRAM bandwidth and compute PPA remain inherited from the source schedule.
- Shared SRAM packing is a macro-level CACTI estimate, not a placed memory compiler floorplan.
