# Decoder Serial Ranker Architecture

- model: `decoder_serial_ranker_architecture_v1`
- decision: `serial_ranker_architecture_measured`
- next_step: Compare serial service time against producer output cadence, then choose a ranker point for producer coupling.

## Variants

| lanes_per_cycle | scan_cycles | materialized | sim | synth | metrics | critical_path_ns | die_area | power_mw |
|---:|---:|---|---|---|---|---:|---:|---:|
| 1 | 64 | `ok` | `ok` | `ok` | `ok` | 2.864771333952124 | 810000.0 | 0.0065519 |
| 2 | 32 | `ok` | `ok` | `ok` | `ok` | 2.927734723812145 | 810000.0 | 0.0075567 |
| 4 | 16 | `ok` | `ok` | `ok` | `ok` | 3.1307233536308563 | 810000.0 | 0.0109817 |
| 8 | 8 | `ok` | `ok` | `ok` | `ok` | 5.772938772211382 | 810000.0 | 0.014957 |
| 16 | 4 | `ok` | `ok` | `ok` | `ok` | 10.071416413790185 | 810000.0 | 0.0842604 |
