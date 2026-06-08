# Llama7B Dense-Tile Topology/Scheduler Pairs

## Summary

- valid pairs: `21708`
- invalid pairs: `36612`
- stored valid row examples: `512`
- stored invalid row examples: `256`
- previous frontier NoC service: `65536.0` B/cycle, `1` hop

## Best Valid Proxy Rows

| topology | scheduler | reduction | bank placement | clusters | banks | local SRAM | link bits | vc | agg B/cyc | worst hops | shared cyc | red cyc | gap to previous BW |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 16 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 16 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 16 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 64 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 64 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 64 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 128 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 128 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | per_cluster_local | 16 | 128 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 16 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 16 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 16 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 64 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 64 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 64 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 128 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 128 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | grouped_shared | 16 | 128 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 16 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 16 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 16 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 64 | 0.05 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 64 | 0.1 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |
| mesh2d | locality_aware | owner_cluster | distributed_shared | 16 | 64 | 0.25 | 2048 | 4 | 3853.5168 | 6 | 1770 | 35 | 17.006803 |

## Common Invalid Reasons

| reason | count |
|---|---:|
| centralized_tile reduction is rejected above 4 clusters | 12960 |
| cluster_tree reduction requires cluster_tree topology or a mesh spanning tree | 9720 |
| tree_reduction_aware scheduler requires cluster_tree reduction | 7776 |
| tree_reduction_aware scheduler requires cluster_tree topology or mesh2d | 5832 |
| ring topology should use owner_cluster or centralized reduction, not cluster_tree | 4860 |
| crossbar does not expose a physical tree reduction fabric | 4860 |
| crossbar is rejected above 8 clusters because switch cost grows quadratically | 4860 |
| bank_aware_prefetch requires shared or distributed banks | 3888 |
| bank_aware_prefetch requires at least 2 virtual channels | 3888 |
| double_buffered_overlap requires at least 2 virtual channels | 3888 |
| centralized_tile bottlenecks a cluster_tree above 4 clusters | 3240 |
| tree_reduction_aware scheduler is not compatible with a plain ring | 2916 |

## Validity Matrix

| topology:scheduler | valid | invalid |
|---|---:|---:|
| cluster_tree:bank_aware_prefetch | 1008 | 1908 |
| cluster_tree:double_buffered_overlap | 1512 | 1404 |
| cluster_tree:locality_aware | 2016 | 900 |
| cluster_tree:static_wave | 2268 | 648 |
| cluster_tree:tree_reduction_aware | 972 | 1944 |
| crossbar:bank_aware_prefetch | 432 | 2484 |
| crossbar:double_buffered_overlap | 648 | 2268 |
| crossbar:locality_aware | 864 | 2052 |
| crossbar:static_wave | 972 | 1944 |
| crossbar:tree_reduction_aware | 0 | 2916 |
| mesh2d:bank_aware_prefetch | 1008 | 1908 |
| mesh2d:double_buffered_overlap | 1512 | 1404 |
| mesh2d:locality_aware | 2016 | 900 |
| mesh2d:static_wave | 1620 | 1296 |
| mesh2d:tree_reduction_aware | 972 | 1944 |
| ring:bank_aware_prefetch | 576 | 2340 |
| ring:double_buffered_overlap | 864 | 2052 |
| ring:locality_aware | 1152 | 1764 |
| ring:static_wave | 1296 | 1620 |
| ring:tree_reduction_aware | 0 | 2916 |

## Notes

- The previous 65kB/cycle, one-hop point is treated as a service target, not a proven topology.
- Valid pairs from this report are candidates for the next scheduler/performance sweep.
