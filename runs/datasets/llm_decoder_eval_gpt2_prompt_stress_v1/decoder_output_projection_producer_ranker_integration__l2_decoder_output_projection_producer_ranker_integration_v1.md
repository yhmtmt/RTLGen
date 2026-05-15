# Decoder Output Projection Producer/Ranker Integration

- model: `decoder_output_projection_producer_ranker_integration_v1`
- decision: `producer_output_ranker_integration_accounting_passed`
- next_step: Use the additive breakdown as the producer-side integration baseline, then decide whether to add clock/path gating or a monolithic routed wrapper.

## Integration Rows

| arch | macro | lanes | bottleneck | cp ns | ranker area/prod | ranker power/prod | serial cycles | ranktree cycles |
|---|---|---:|---|---:|---:|---:|---:|---:|
| fp16_nm1 | flat_nomacro | 64 | producer | 5.5570 | 0.0604 | 0.0836 | 1987 | 35 |
| fp16_nm1 | hier_macro | 64 | producer | 5.7749 | 0.0604 | 0.0818 | 1987 | 35 |
| fp16_nm2 | flat_nomacro | 128 | producer | 5.7013 | 0.1233 | 0.1448 | 1987 | 20 |
| fp16_nm2 | hier_macro | 128 | producer | 5.7409 | 0.1233 | 0.1432 | 1987 | 20 |

## Checks

| check | passed | observed |
|---|---|---|
| ranker_wrapper_physical_measured | `True` | `output_projection_ranker_wrapper_physical_measured` |
| ranker_policy_promoted | `True` | `output_projection_ranker_policy_promoted` |
| all_producer_arches_have_ranker_mapping | `True` | `{'ok': 4, 'total': 4}` |
| ranker_not_timing_bottleneck | `True` | `[{'arch_id': 'fp16_nm1', 'macro_mode': 'flat_nomacro', 'timing_bottleneck': 'producer'}, {'arch_id': 'fp16_nm1', 'macro_mode': 'hier_macro', 'timing_bottleneck': 'producer'}, {'arch_id': 'fp16_nm2', 'macro_mode': 'flat_nomacro', 'timing_bottleneck': 'producer'}, {'arch_id': 'fp16_nm2', 'macro_mode': 'hier_macro', 'timing_bottleneck': 'producer'}]` |
| ranker_overhead_within_first_order_budget | `True` | `{'max_ranker_area_over_producer': 0.123332, 'max_ranker_power_over_producer': 0.14483589494995577, 'budget': {'area': 0.15, 'power': 0.2}}` |
