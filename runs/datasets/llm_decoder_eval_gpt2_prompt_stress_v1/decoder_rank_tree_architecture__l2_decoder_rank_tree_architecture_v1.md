# Decoder Rank Tree Architecture

- model: `decoder_rank_tree_architecture_v1`
- decision: `rank_tree_architecture_measured`
- next_step: Use the best radix as the r64 ranker anchor, then test producer-coupled timing and r128 scaling.

## Variants

| radix | stages | materialized | sim | synth | metrics | critical_path_ns | die_area | power_mw |
|---:|---:|---|---|---|---|---:|---:|---:|
| 2 | 6 | `ok` | `ok` | `ok` | `ok` | 3.0732257499439135 | 810000.0 | 0.0150608 |
| 4 | 3 | `ok` | `ok` | `ok` | `ok` | 4.35477479282159 | 810000.0 | 0.0114306 |
| 8 | 2 | `ok` | `ok` | `ok` | `ok` | 6.867424372489098 | 810000.0 | 0.0156103 |
