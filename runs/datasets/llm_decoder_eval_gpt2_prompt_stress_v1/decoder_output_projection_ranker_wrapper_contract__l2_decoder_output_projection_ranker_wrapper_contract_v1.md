# Decoder Output-Projection Ranker Wrapper Contract

- model: `decoder_output_projection_ranker_wrapper_contract_v1`
- decision: `output_projection_ranker_wrapper_contract_passed`
- next_step: Implement the wrapper RTL mux/control around the verified serial_lpc1 and rank-tree primitive paths, then run a physical wrapper sweep.

## Representative Cases

| case | passed | reason |
|---|---|---|
| streaming_serial_lpc1_r64 | `True` | serial RTL replay matches perf reference with zero backpressure |
| resident_ranktree_r64 | `True` | rank-tree r64 RTL primitive matches perf reference |
| resident_ranktree_banked_r128 | `True` | banked r64 composition matches full r128 perf reference |

## Checks

| check | passed | observed |
|---|---|---|
| ranker_policy_promoted | `True` | `output_projection_ranker_policy_promoted` |
| representative_cases_passed | `True` | `{'streaming_serial_lpc1_r64': True, 'resident_ranktree_r64': True, 'resident_ranktree_banked_r128': True}` |

## Assumptions

- The serial path is checked by a fresh RTL replay of the promoted serial_lpc1 wrapper at the policy threshold.
- The r64 rank-tree path reuses the promoted rank-tree primitive RTL simulation from the rank-tree architecture sweep.
- The r128 banked path is a composition contract: two proven r64 primitives plus deterministic lower-token tie-break across banks.
- This job does not synthesize the final wrapper mux/control; it establishes the contract that the next RTL wrapper must implement.
