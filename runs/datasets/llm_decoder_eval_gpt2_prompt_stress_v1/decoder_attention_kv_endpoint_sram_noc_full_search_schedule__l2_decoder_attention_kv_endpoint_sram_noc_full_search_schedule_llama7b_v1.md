# Llama7B Practical SRAM/NoC Constrained Schedule

- source rows used: `746496`
- generated rows: `35831808`
- infeasible counts: `{}`
- NoC cap sources: `{'endpoint': 15256512, 'sram_bank': 20575296}`

## Best

| topology | scheduler | reduction | clusters | link bits | endpoint B/cyc/cluster | SRAM bank B/cyc/cluster | NoC agg B/cyc | replicas | die | latency us | slowdown | resource | cap |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| mesh2d | locality_aware | cluster_tree | 16 | 2048 | 108.8 | 108.8 | 1740.8 | 856 | 800.0 | 3244.14864 | 1.520452 | shared_path | endpoint |

## Best By Endpoint/SRAM Setting

| endpoint B/cyc | endpoint ports | bank eff | buffer x | topology | latency us | slowdown | resource |
|---:|---:|---:|---:|---|---:|---:|---|
| 64.0 | 2 | 0.85 | 1.0 | mesh2d/locality_aware | 3244.14864 | 1.520452 | shared_path |
| 128.0 | 1 | 0.85 | 1.0 | mesh2d/locality_aware | 3244.14864 | 1.520452 | shared_path |
| 128.0 | 2 | 0.85 | 1.0 | mesh2d/locality_aware | 3244.14864 | 1.520452 | shared_path |
| 64.0 | 2 | 0.85 | 2.0 | mesh2d/locality_aware | 3244.14864 | 1.520452 | shared_path |
| 128.0 | 1 | 0.85 | 2.0 | mesh2d/locality_aware | 3244.14864 | 1.520452 | shared_path |
| 128.0 | 2 | 0.85 | 2.0 | mesh2d/locality_aware | 3244.14864 | 1.520452 | shared_path |
| 64.0 | 2 | 0.7 | 1.0 | mesh2d/locality_aware | 3923.98439 | 1.839074 | shared_path |
| 128.0 | 1 | 0.7 | 1.0 | mesh2d/locality_aware | 3923.98439 | 1.839074 | shared_path |
| 128.0 | 2 | 0.7 | 1.0 | mesh2d/locality_aware | 3923.98439 | 1.839074 | shared_path |
| 64.0 | 2 | 0.7 | 2.0 | mesh2d/locality_aware | 3923.98439 | 1.839074 | shared_path |
| 128.0 | 1 | 0.7 | 2.0 | mesh2d/locality_aware | 3923.98439 | 1.839074 | shared_path |
| 128.0 | 2 | 0.7 | 2.0 | mesh2d/locality_aware | 3923.98439 | 1.839074 | shared_path |
| 32.0 | 2 | 0.7 | 1.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 64.0 | 1 | 0.7 | 1.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 32.0 | 2 | 0.85 | 1.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 64.0 | 1 | 0.85 | 1.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 32.0 | 2 | 0.7 | 2.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 64.0 | 1 | 0.7 | 2.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 32.0 | 2 | 0.85 | 2.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 64.0 | 1 | 0.85 | 2.0 | mesh2d/locality_aware | 6416.14129 | 3.007086 | shared_path |
| 32.0 | 1 | 0.7 | 1.0 | mesh2d/locality_aware | 12758.595427 | 5.979638 | shared_path |
| 32.0 | 1 | 0.85 | 1.0 | mesh2d/locality_aware | 12758.595427 | 5.979638 | shared_path |
| 32.0 | 1 | 0.7 | 2.0 | mesh2d/locality_aware | 12758.595427 | 5.979638 | shared_path |
| 32.0 | 1 | 0.85 | 2.0 | mesh2d/locality_aware | 12758.595427 | 5.979638 | shared_path |

## Best By Topology

| topology | scheduler | reduction | clusters | link bits | latency us | slowdown | resource | cap |
|---|---|---|---:|---:|---:|---:|---|---|
| mesh2d | locality_aware | cluster_tree | 16 | 2048 | 3244.14864 | 1.520452 | shared_path | endpoint |
| mesh2d | tree_reduction_aware | cluster_tree | 16 | 2048 | 3244.14864 | 1.520452 | shared_path | endpoint |
| mesh2d | locality_aware | owner_cluster | 16 | 2048 | 3269.412806 | 1.514362 | shared_path | endpoint |
| mesh2d | double_buffered_overlap | owner_cluster | 16 | 2048 | 3269.412806 | 1.514362 | shared_path | endpoint |
| mesh2d | bank_aware_prefetch | cluster_tree | 16 | 2048 | 3874.987219 | 1.816111 | shared_path | endpoint |
| mesh2d | bank_aware_prefetch | owner_cluster | 16 | 2048 | 3900.251386 | 1.80656 | shared_path | endpoint |

## Assumptions

- Input rows are regenerated from the topology/scheduler pair matrix before practical SRAM/NoC caps are applied.
- SRAM bank service is capped by measured 256-bit tile-buffer bank width unless overridden by the CLI.
- NoC service is capped by the minimum of topology aggregate payload service, endpoint injection/ejection service, and practical SRAM bank read service.
- Local tile-buffer capacity is required per cluster; full KV-cache residency remains the higher-level HBM/SRAM capacity model from the source schedule.
- This is still analytic scheduling evidence, not cycle-accurate SRAM arbitration or routed NoC RTL.
