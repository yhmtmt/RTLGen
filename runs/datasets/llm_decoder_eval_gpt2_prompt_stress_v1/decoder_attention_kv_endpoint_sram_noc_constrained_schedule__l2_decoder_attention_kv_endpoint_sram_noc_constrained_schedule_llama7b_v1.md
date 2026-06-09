# Llama7B Practical SRAM/NoC Constrained Schedule

- source rows used: `25`
- generated rows: `1200`
- infeasible counts: `{}`
- NoC cap sources: `{'endpoint': 510, 'sram_bank': 690}`

## Best

| topology | scheduler | reduction | clusters | link bits | endpoint B/cyc/cluster | SRAM bank B/cyc/cluster | NoC agg B/cyc | replicas | die | latency us | slowdown | resource | cap |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| mesh2d | locality_aware | cluster_tree | 16 | 2048 | 108.8 | 108.8 | 1740.8 | 856 | 800.0 | 4086.28752 | 1.915142 | shared_path | endpoint |

## Best By Endpoint/SRAM Setting

| endpoint B/cyc | endpoint ports | bank eff | buffer x | topology | latency us | slowdown | resource |
|---:|---:|---:|---:|---|---:|---:|---|
| 64.0 | 2 | 0.85 | 1.0 | mesh2d/locality_aware | 4086.28752 | 1.915142 | shared_path |
| 128.0 | 1 | 0.85 | 1.0 | mesh2d/locality_aware | 4086.28752 | 1.915142 | shared_path |
| 128.0 | 2 | 0.85 | 1.0 | mesh2d/locality_aware | 4086.28752 | 1.915142 | shared_path |
| 64.0 | 2 | 0.85 | 2.0 | mesh2d/locality_aware | 4086.28752 | 1.915142 | shared_path |
| 128.0 | 1 | 0.85 | 2.0 | mesh2d/locality_aware | 4086.28752 | 1.915142 | shared_path |
| 128.0 | 2 | 0.85 | 2.0 | mesh2d/locality_aware | 4086.28752 | 1.915142 | shared_path |
| 64.0 | 2 | 0.7 | 1.0 | mesh2d/locality_aware | 4945.269178 | 2.317725 | shared_path |
| 128.0 | 1 | 0.7 | 1.0 | mesh2d/locality_aware | 4945.269178 | 2.317725 | shared_path |
| 128.0 | 2 | 0.7 | 1.0 | mesh2d/locality_aware | 4945.269178 | 2.317725 | shared_path |
| 64.0 | 2 | 0.7 | 2.0 | mesh2d/locality_aware | 4945.269178 | 2.317725 | shared_path |
| 128.0 | 1 | 0.7 | 2.0 | mesh2d/locality_aware | 4945.269178 | 2.317725 | shared_path |
| 128.0 | 2 | 0.7 | 2.0 | mesh2d/locality_aware | 4945.269178 | 2.317725 | shared_path |
| 32.0 | 2 | 0.7 | 1.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 64.0 | 1 | 0.7 | 1.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 32.0 | 2 | 0.85 | 1.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 64.0 | 1 | 0.85 | 1.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 32.0 | 2 | 0.7 | 2.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 64.0 | 1 | 0.7 | 2.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 32.0 | 2 | 0.85 | 2.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 64.0 | 1 | 0.85 | 2.0 | mesh2d/locality_aware | 8098.887888 | 3.795748 | shared_path |
| 32.0 | 1 | 0.7 | 1.0 | mesh2d/locality_aware | 16125.619786 | 7.557679 | shared_path |
| 32.0 | 1 | 0.85 | 1.0 | mesh2d/bank_aware_prefetch | 16125.619786 | 7.557679 | shared_path |
| 32.0 | 1 | 0.7 | 2.0 | mesh2d/locality_aware | 16125.619786 | 7.557679 | shared_path |
| 32.0 | 1 | 0.85 | 2.0 | mesh2d/bank_aware_prefetch | 16125.619786 | 7.557679 | shared_path |

## Best By Topology

| topology | scheduler | reduction | clusters | link bits | latency us | slowdown | resource | cap |
|---|---|---|---:|---:|---:|---:|---|---|
| mesh2d | locality_aware | cluster_tree | 16 | 2048 | 4086.28752 | 1.915142 | shared_path | endpoint |
| mesh2d | bank_aware_prefetch | cluster_tree | 16 | 2048 | 16125.619786 | 7.557679 | shared_path | endpoint |
| mesh2d | tree_reduction_aware | cluster_tree | 16 | 2048 | 16125.619786 | 7.557679 | shared_path | endpoint |
| mesh2d | bank_aware_prefetch | owner_cluster | 16 | 2048 | 16150.883952 | 7.48094 | shared_path | endpoint |
| mesh2d | double_buffered_overlap | owner_cluster | 16 | 2048 | 16150.883952 | 7.48094 | shared_path | endpoint |
| mesh2d | locality_aware | owner_cluster | 16 | 2048 | 16150.883952 | 7.48094 | shared_path | endpoint |

## Assumptions

- Input rows are retained frontier rows from the topology-derived scheduler, not a full re-search of all generated rows.
- SRAM bank service is capped by measured 256-bit tile-buffer bank width unless overridden by the CLI.
- NoC service is capped by the minimum of topology aggregate payload service, endpoint injection/ejection service, and practical SRAM bank read service.
- Local tile-buffer capacity is required per cluster; full KV-cache residency remains the higher-level HBM/SRAM capacity model from the source schedule.
- This is still analytic scheduling evidence, not cycle-accurate SRAM arbitration or routed NoC RTL.
