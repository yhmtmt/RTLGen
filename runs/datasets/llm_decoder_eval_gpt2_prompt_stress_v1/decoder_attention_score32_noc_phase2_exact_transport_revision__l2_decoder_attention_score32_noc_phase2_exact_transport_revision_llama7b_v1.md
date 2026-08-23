# Llama7B Phase-2 Exact Transport Revision

- decision: `prior_phase2_reduction_contract_retracted_exact_transport_required`
- prior commands/flits: `11576` / `92128`
- exact release: one aggregate stream per head group after eight local waves

| Mode | Commands | Flits | Ratio vs prior | Reduction packets/cluster |
|---|---:|---:|---:|---:|
| `aligned_419b_two_flits_per_beat` | 9536 | 76288 | 0.828 | 128 |
| `packed_419b_group_bitstream` | 9236 | 73528 | 0.798 | 108 |
| `stats_once_ordered_exact` | 8876 | 70948 | 0.770 | 84 |

## Recommendation

Implement aligned transport as the direct field-preserving equivalence anchor, then implement stats-once ordered packing and compare codec PPA plus actual producer/root backpressure before rebuilding the Phase-2 command schedule.
