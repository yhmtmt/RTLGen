# Decoder Resident-Weight Ranker Fallback

- model: `decoder_resident_weight_ranker_fallback_v1`
- decision: `rank_tree_fallback_preferred_for_resident_weight`
- unsafe_rows: `32`
- rank_tree_recommended_rows: `32`
- buffered_serial_recommended_rows: `0`
- next_step: Promote a rank-tree fallback wrapper for resident-weight producer rows, while keeping buffered serial_lpc4 only for near-threshold cadence cases.

## Fallback Rows

| vocab | hidden | W | prod II | hit | recommended | buffer r64 tiles | buffer bytes | power mW |
|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 50257 | 768 | 64 | 6 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 768 | 64 | 6 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 768 | 64 | 2 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 768 | 64 | 2 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 768 | 128 | 12 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 768 | 128 | 12 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 768 | 128 | 3 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 768 | 128 | 3 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 2048 | 64 | 16 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 2048 | 64 | 16 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 2048 | 64 | 4 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 2048 | 64 | 4 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 50257 | 2048 | 128 | 32 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 2048 | 128 | 32 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 2048 | 128 | 8 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 50257 | 2048 | 128 | 8 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 768 | 64 | 6 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 768 | 64 | 6 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 768 | 64 | 2 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 768 | 64 | 2 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 768 | 128 | 12 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 768 | 128 | 12 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 768 | 128 | 3 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 768 | 128 | 3 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 2048 | 64 | 16 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 2048 | 64 | 16 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 2048 | 64 | 4 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 2048 | 64 | 4 | 1.0 | single_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0114306 |
| 100000 | 2048 | 128 | 32 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 2048 | 128 | 32 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 2048 | 128 | 8 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |
| 100000 | 2048 | 128 | 8 | 1.0 | banked_r64_ranktrees_ranktree_radix4 | 0 | 0 | 0.0228612 |

## Assumptions

- Unsafe rows are producer cadence rows where prior serial replay has no zero-backpressure ranker.
- Buffer depth is simulated as r64 logit-tile chunks waiting in front of the ranker, excluding the tile in service.
- Rank-tree fallback reuses measured r64/k1 rank-tree variants; single_r64 handles wider producer tiles sequentially, banked_r64 duplicates r64 rankers.
- The model ignores SRAM/FIFO implementation overhead beyond raw logit storage bytes.
