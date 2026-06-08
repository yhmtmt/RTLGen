# Llama7B Topology-Derived Clustered Schedule

- topology rows used: `128`
- generated rows: `746496`
- skipped area-budget rows: `248832`

## Best

| topology | scheduler | reduction | clusters | link bits | hops | agg B/cyc | gap | replicas | die | SRAM | logic | latency us | resource |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| mesh2d | locality_aware | cluster_tree | 16 | 2048 | 6 | 3853.5168 | 17.006803 | 856 | 800.0 | 0.35 | 0.5 | 2133.67369 | tile_attention |

## Best By Scheduler

| topology | scheduler | reduction | clusters | link bits | hops | agg B/cyc | latency us | resource |
|---|---|---|---:|---:|---:|---:|---:|---|
| mesh2d | locality_aware | cluster_tree | 16 | 2048 | 6 | 3853.5168 | 2133.67369 | tile_attention |
| mesh2d | tree_reduction_aware | cluster_tree | 16 | 2048 | 6 | 3853.5168 | 2133.67369 | tile_attention |
| mesh2d | bank_aware_prefetch | cluster_tree | 16 | 2048 | 6 | 3853.5168 | 2133.67369 | tile_attention |
| mesh2d | locality_aware | owner_cluster | 16 | 2048 | 6 | 3853.5168 | 2158.937856 | tile_attention |
| mesh2d | bank_aware_prefetch | owner_cluster | 16 | 2048 | 6 | 3853.5168 | 2158.937856 | tile_attention |
| mesh2d | double_buffered_overlap | owner_cluster | 16 | 2048 | 6 | 3853.5168 | 2158.937856 | tile_attention |

## Best By Die And Topology

| die | topology | scheduler | clusters | link bits | replicas | latency us | resource |
|---:|---|---|---:|---:|---:|---:|---|
| 800.0 | mesh2d | locality_aware | 16 | 2048 | 856 | 2133.67369 | tile_attention |
| 1200.0 | mesh2d | locality_aware | 16 | 2048 | 1288 | 2202.958752 | shared_path |

## Assumptions

- NoC service rows come from the logically valid topology/scheduler pair matrix.
- The clustered scheduler preserves topology worst-hop latency while using the topology-derived aggregate payload service for bandwidth.
- This remains analytic schedule evidence; it is not cycle-accurate NoC RTL or SRAM arbitration.
