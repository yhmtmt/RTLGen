# Decoder Output-Projection Ranker Policy

- model: `decoder_output_projection_ranker_policy_v1`
- decision: `output_projection_ranker_policy_promoted`
- serial_lpc1_min_ii_cycles: `384`
- total_rows: `128`
- serial_lpc1_rows: `68`
- ranktree_rows: `60`
- uncovered_rows: `0`
- next_step: Implement the output-projection producer wrapper policy with a serial_lpc1 path for streaming/slow producer cadences and a radix-4 rank-tree fallback path for faster resident/cache-backed cadences.

## Path Counts

| path | rows |
|---|---:|
| banked_r64_ranktrees | 28 |
| serial_lpc1 | 68 |
| single_r64_ranktree | 32 |

## Checks

| check | passed | observed |
|---|---|---|
| serial_lpc1_wrapper_promoted | `True` | `serial_lpc1_producer_coupled_wrapper_promoted` |
| resident_ranktree_fallback_promoted | `True` | `resident_weight_ranktree_fallback_promoted` |
| serial_lpc1_threshold_available | `True` | `384` |
| all_cadence_rows_covered | `True` | `{'total_rows': 128, 'uncovered_rows': 0}` |
| ranktree_has_single_and_banked_modes | `True` | `['banked_r64_ranktrees', 'single_r64_ranktree']` |

## Assumptions

- The policy is conservative: lpc2/lpc4 rows that were analytically safe are routed to the promoted rank-tree unless lpc1 is also safe.
- The rank-tree fallback uses one r64 rank-tree for producer_lanes <= 64 and banked r64 rank-trees for wider producer tiles.
- The selection boundary is replay-observed ready-valid backpressure, not only analytical ranker service cycles.
- Future measured producer burst traces may add hysteresis or buffering around this fixed-II policy boundary.
