# Decoder Pipelined Ranker Architecture

- model: `decoder_pipelined_ranker_architecture_v1`
- decision: `pipelined_ranker_architecture_measured`
- next_step: Compare the best pipelined r64 point against the unpipelined wrapper, then decide whether to scale r128 or tune register cuts.

## Variants

| local_lanes | groups | materialized | sim | synth | metrics | critical_path_ns | die_area | power_mw |
|---:|---:|---|---|---|---|---:|---:|---:|
| 8 | 8 | `ok` | `ok` | `ok` | `ok` | 6.635964271968359 | 810000.0 | 0.0143868 |
| 16 | 4 | `ok` | `ok` | `ok` | `ok` | 10.302088130243119 | 810000.0 | 0.105272 |
| 32 | 2 | `ok` | `ok` | `ok` | `ok` | 17.2747075823874 | 810000.0 | 1.31634 |
