# Llama7B On-Chip SRAM/NoC Service Schedule

- source rows used: `13`
- generated rows: `8424`
- dominant resources: `{'shared_path': 8424}`

## Best

| topology | schedule | bank policy | clusters | link bits | endpoint q | bank q | router hop | packet | latency us | vs cap | vs topo | resource |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| mesh2d | prefetch_overlap | locality_first | 16 | 2048 | 2048 | 2048 | 1 | 128 | 4065.042653 | 0.994801 | 1.905185 | shared_path |

## Best By Policy

| schedule | bank policy | latency us | vs cap | shared service cycles | exposed shared | resource |
|---|---|---:|---:|---:|---:|---|
| prefetch_overlap | locality_first | 4065.042653 | 0.994801 | 3170 | 2493 | shared_path |
| prefetch_overlap | age_based | 4274.811792 | 1.046136 | 3306 | 2629 | shared_path |
| static_wave | locality_first | 4463.144669 | 1.092225 | 2872 | 2872 | shared_path |
| staggered_wave | locality_first | 4509.079517 | 1.103466 | 2902 | 2902 | shared_path |
| prefetch_overlap | round_robin | 4509.270912 | 1.103513 | 3458 | 2781 | shared_path |
| static_wave | age_based | 4648.415222 | 1.137564 | 2993 | 2993 | shared_path |
| staggered_wave | age_based | 4694.35007 | 1.148806 | 3023 | 3023 | shared_path |
| static_wave | round_robin | 4856.844595 | 1.188571 | 3129 | 3129 | shared_path |
| staggered_wave | round_robin | 4902.779443 | 1.199813 | 3159 | 3159 | shared_path |

## Best By Queue/Router Setting

| endpoint q | bank q | router hop | latency us | queue penalties | resource |
|---:|---:|---:|---:|---|---|
| 2048 | 2048 | 1 | 4065.042653 | endpoint=0,bank=537 | shared_path |
| 2048 | 8192 | 1 | 4065.042653 | endpoint=0,bank=480 | shared_path |
| 2048 | 32768 | 1 | 4065.042653 | endpoint=0,bank=254 | shared_path |
| 8192 | 2048 | 1 | 4065.042653 | endpoint=0,bank=537 | shared_path |
| 8192 | 8192 | 1 | 4065.042653 | endpoint=0,bank=480 | shared_path |
| 8192 | 32768 | 1 | 4065.042653 | endpoint=0,bank=254 | shared_path |
| 32768 | 2048 | 1 | 4065.042653 | endpoint=0,bank=537 | shared_path |
| 32768 | 8192 | 1 | 4065.042653 | endpoint=0,bank=480 | shared_path |
| 32768 | 32768 | 1 | 4065.042653 | endpoint=0,bank=254 | shared_path |
| 2048 | 2048 | 2 | 4069.636138 | endpoint=0,bank=537 | shared_path |
| 2048 | 8192 | 2 | 4069.636138 | endpoint=0,bank=480 | shared_path |
| 2048 | 32768 | 2 | 4069.636138 | endpoint=0,bank=254 | shared_path |
| 8192 | 2048 | 2 | 4069.636138 | endpoint=0,bank=537 | shared_path |
| 8192 | 8192 | 2 | 4069.636138 | endpoint=0,bank=480 | shared_path |
| 8192 | 32768 | 2 | 4069.636138 | endpoint=0,bank=254 | shared_path |
| 32768 | 2048 | 2 | 4069.636138 | endpoint=0,bank=537 | shared_path |
| 32768 | 8192 | 2 | 4069.636138 | endpoint=0,bank=480 | shared_path |
| 32768 | 32768 | 2 | 4069.636138 | endpoint=0,bank=254 | shared_path |

## Assumptions

- This pass refines on-chip SRAM/NoC service only; HBM/DRAM cycles and bandwidth fields are inherited from the input row.
- SRAM bank arbitration is modeled as per-cycle service under a named policy, not as placed SRAM macro RTL.
- Endpoint queues, packet payload, router hop latency, and schedule staggering are explicit parameters.
- The model is still an analytic service simulator; it does not yet generate RTL routers or prove ready/valid equivalence.
