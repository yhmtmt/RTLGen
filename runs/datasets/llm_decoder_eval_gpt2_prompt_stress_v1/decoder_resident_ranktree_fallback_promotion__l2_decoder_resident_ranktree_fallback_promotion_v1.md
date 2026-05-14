# Decoder Resident Rank-Tree Fallback Promotion

- model: `decoder_resident_ranktree_fallback_promotion_v1`
- decision: `resident_weight_ranktree_fallback_promoted`
- selected_radix: `4`
- unsafe_rows: `32`
- max_required_buffer_r64_tiles: `0`
- critical_path_ns: `4.35477479282159`
- placed_cell_area_um2: `24452.316`
- total_power_mw: `0.0114306`
- next_step: Implement or instantiate the radix-4 r64 rank-tree fallback in the resident-weight output-projection producer wrapper: one instance for r64 producer tiles and two banked instances for r128 producer tiles.

## Producer Modes

| mode | lanes | instances | II | rows | max buffer r64 | power mW | area um2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| single_r64_ranktree | 64 | 1 | 1 | 16 | 0 | 0.0114306 | 24452.316 |
| banked_r64_ranktrees | 128 | 2 | 1 | 16 | 0 | 0.0228612 | 48904.632 |

## Checks

| check | passed | observed |
|---|---|---|
| fallback_prefers_rank_tree | `True` | `{'buffered_serial_recommended_rows': 0, 'decision': 'rank_tree_fallback_preferred_for_resident_weight', 'next_step': 'Promote a rank-tree fallback wrapper for resident-weight producer rows, while keeping buffered serial_lpc4 only for near-threshold cadence cases.', 'rank_tree_recommended_rows': 32, 'unsafe_rows': 32}` |
| all_unsafe_rows_have_rank_tree_strategy | `True` | `{'single_r64_ranktrees_ranktree_radix4': 16, 'banked_r64_ranktrees_ranktree_radix4': 16}` |
| rank_tree_strategy_has_single_radix | `True` | `[4]` |
| selected_rank_tree_variant_has_clean_rtl_sim | `True` | `{'expected': {'logit': 500, 'token': 5}, 'log_tail': ['RESULT token=5 logit=500 accepted=3 stalls=0 fifo_max=1 final_cycle=10', '/tmp/rtlcp-worktree-nh2cvu6u/repo/runs/designs/activations/decoder_r64_k1_ranktree_radix4_pipe3_wrapper/tb_decoder_r64_k1_ranktree_radix4_pipe3_wrapper.v:293: $finish called at 140000 (1ps)'], 'returncode': 0, 'status': 'ok'}` |
| selected_rank_tree_variant_has_physical_metrics | `True` | `{'top': 'decoder_r64_k1_ranktree_radix4_pipe3_wrapper', 'radix': 4, 'pipeline_stages': 3, 'critical_path_ns': 4.35477479282159, 'die_area_um2': 810000.0, 'placed_cell_area_um2': 24452.316, 'total_power_mw': 0.0114306, 'metrics_status': 'ok', 'simulation_status': 'ok', 'design_dir': 'runs/designs/activations/decoder_r64_k1_ranktree_radix4_pipe3_wrapper'}` |
| promotion_requires_no_waiting_buffer | `True` | `0` |

## Assumptions

- The fallback policy is for resident/cache-backed output-projection rows that outpace the replay-proven serial ranker thresholds.
- Single-r64 mode uses one measured r64/k1 rank-tree instance at II=1.
- Banked-r64 mode duplicates the measured r64/k1 rank-tree per 64-lane chunk so r128 producer tiles still drain at II=1.
- This promotion carries measured rank-tree PPA and RTL simulation status; it does not model FIFO/SRAM overhead because the selected current rows require no waiting buffer.
