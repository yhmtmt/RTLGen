# Llama7B Dense-Tile Topology/Scheduler Pairs

## Summary

- valid pairs: `27432`
- invalid pairs: `94068`
- stored valid row examples: `512`
- stored invalid row examples: `256`
- previous frontier NoC service: `32768.0` B/cycle, `1` hop

## Best Valid Proxy Rows

| topology | scheduler | reduction | bank placement | clusters | banks | local SRAM | link bits | vc | agg B/cyc | worst hops | shared cyc | red cyc | gap to previous BW |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 16 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 16 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 16 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 64 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 64 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 64 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 128 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 128 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 128 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 16 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 16 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 16 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 64 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 64 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 64 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 128 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 128 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 128 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 16 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 16 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 16 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 64 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 64 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 64 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 958 | 35 | 8.503401 |

## Common Invalid Reasons

| reason | count |
|---|---:|
| local_only topology cannot serve shared-KV traffic | 24300 |
| cluster_tree reduction requires cluster_tree topology or a mesh spanning tree | 24300 |
| local_only topology cannot route between multiple clusters | 19440 |
| local_only topology requires owner_cluster reduction | 16200 |
| local_only topology requires per_cluster_local banks | 16200 |
| grouped_shared placement is not meaningful below 4 clusters | 16200 |
| tree_reduction_aware scheduler requires cluster_tree reduction | 16200 |
| centralized_tile reduction is rejected above 4 clusters | 16200 |
| tree_reduction_aware scheduler requires cluster_tree topology or mesh2d | 14580 |
| mesh2d topology requires at least 4 clusters | 9720 |
| bank_aware_prefetch requires shared or distributed banks | 8100 |
| bank_aware_prefetch requires at least 2 virtual channels | 8100 |

## Validity Matrix

| topology:scheduler | valid | invalid |
|---|---:|---:|
| cluster_tree:bank_aware_prefetch | 1224 | 3636 |
| cluster_tree:double_buffered_overlap | 1944 | 2916 |
| cluster_tree:locality_aware | 2556 | 2304 |
| cluster_tree:static_wave | 2916 | 1944 |
| cluster_tree:tree_reduction_aware | 1188 | 3672 |
| crossbar:bank_aware_prefetch | 720 | 4140 |
| crossbar:double_buffered_overlap | 1224 | 3636 |
| crossbar:locality_aware | 1584 | 3276 |
| crossbar:static_wave | 1836 | 3024 |
| crossbar:tree_reduction_aware | 0 | 4860 |
| local_only:bank_aware_prefetch | 0 | 4860 |
| local_only:double_buffered_overlap | 0 | 4860 |
| local_only:locality_aware | 0 | 4860 |
| local_only:static_wave | 0 | 4860 |
| local_only:tree_reduction_aware | 0 | 4860 |
| mesh2d:bank_aware_prefetch | 1008 | 3852 |
| mesh2d:double_buffered_overlap | 1512 | 3348 |
| mesh2d:locality_aware | 2016 | 2844 |
| mesh2d:static_wave | 1620 | 3240 |
| mesh2d:tree_reduction_aware | 972 | 3888 |
| ring:bank_aware_prefetch | 720 | 4140 |
| ring:double_buffered_overlap | 1152 | 3708 |
| ring:locality_aware | 1512 | 3348 |
| ring:static_wave | 1728 | 3132 |
| ring:tree_reduction_aware | 0 | 4860 |

## Notes

- The previous 65kB/cycle, one-hop point is treated as a service target, not a proven topology.
- Valid pairs from this report are candidates for the next scheduler/performance sweep.
