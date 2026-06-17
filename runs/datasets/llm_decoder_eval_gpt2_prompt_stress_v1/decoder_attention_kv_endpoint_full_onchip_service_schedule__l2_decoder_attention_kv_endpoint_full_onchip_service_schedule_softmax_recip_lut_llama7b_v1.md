# Llama7B On-Chip SRAM/NoC Service Schedule

- source rows used: `14`
- generated rows: `9072`
- dominant resources: `{'shared_path': 9072}`

## Best

| topology | schedule | bank policy | clusters | link bits | endpoint q | bank q | router hop | packet | latency us | vs cap | vs topo | resource |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| mesh2d | prefetch_overlap | locality_first | 16 | 2048 | 2048 | 2048 | 1 | 128 | 3222.903773 | 0.993451 | 1.510495 | shared_path |

## Best By Policy

| schedule | bank policy | latency us | vs cap | shared service cycles | exposed shared | resource |
|---|---|---:|---:|---:|---:|---|
| prefetch_overlap | locality_first | 3222.903773 | 0.993451 | 2503 | 1826 | shared_path |
| prefetch_overlap | age_based | 3389.800387 | 1.044897 | 2611 | 1934 | shared_path |
| static_wave | locality_first | 3441.859882 | 1.060944 | 2205 | 2205 | shared_path |
| staggered_wave | locality_first | 3487.79473 | 1.075103 | 2235 | 2235 | shared_path |
| prefetch_overlap | round_robin | 3573.731174 | 1.101593 | 2730 | 2053 | shared_path |
| static_wave | age_based | 3584.25791 | 1.104838 | 2298 | 2298 | shared_path |
| staggered_wave | age_based | 3630.192758 | 1.118997 | 2328 | 2328 | shared_path |
| static_wave | round_robin | 3742.15895 | 1.15351 | 2401 | 2401 | shared_path |
| staggered_wave | round_robin | 3788.093798 | 1.16767 | 2431 | 2431 | shared_path |

## Best By Queue/Router Setting

| endpoint q | bank q | router hop | latency us | queue penalties | resource |
|---:|---:|---:|---:|---|---|
| 2048 | 2048 | 1 | 3222.903773 | endpoint=0,bank=420 | shared_path |
| 2048 | 8192 | 1 | 3222.903773 | endpoint=0,bank=363 | shared_path |
| 2048 | 32768 | 1 | 3222.903773 | endpoint=0,bank=575 | shared_path |
| 8192 | 2048 | 1 | 3222.903773 | endpoint=0,bank=420 | shared_path |
| 8192 | 8192 | 1 | 3222.903773 | endpoint=0,bank=363 | shared_path |
| 8192 | 32768 | 1 | 3222.903773 | endpoint=0,bank=575 | shared_path |
| 32768 | 2048 | 1 | 3222.903773 | endpoint=0,bank=420 | shared_path |
| 32768 | 8192 | 1 | 3222.903773 | endpoint=0,bank=363 | shared_path |
| 32768 | 32768 | 1 | 3222.903773 | endpoint=0,bank=575 | shared_path |
| 2048 | 2048 | 2 | 3227.497258 | endpoint=0,bank=420 | shared_path |
| 2048 | 8192 | 2 | 3227.497258 | endpoint=0,bank=363 | shared_path |
| 2048 | 32768 | 2 | 3227.497258 | endpoint=0,bank=575 | shared_path |
| 8192 | 2048 | 2 | 3227.497258 | endpoint=0,bank=420 | shared_path |
| 8192 | 8192 | 2 | 3227.497258 | endpoint=0,bank=363 | shared_path |
| 8192 | 32768 | 2 | 3227.497258 | endpoint=0,bank=575 | shared_path |
| 32768 | 2048 | 2 | 3227.497258 | endpoint=0,bank=420 | shared_path |
| 32768 | 8192 | 2 | 3227.497258 | endpoint=0,bank=363 | shared_path |
| 32768 | 32768 | 2 | 3227.497258 | endpoint=0,bank=575 | shared_path |

## Assumptions

- This pass refines on-chip SRAM/NoC service only; HBM/DRAM cycles and bandwidth fields are inherited from the input row.
- SRAM bank arbitration is modeled as per-cycle service under a named policy, not as placed SRAM macro RTL.
- Endpoint queues, packet payload, router hop latency, and schedule staggering are explicit parameters.
- The model is still an analytic service simulator; it does not yet generate RTL routers or prove ready/valid equivalence.
