# Score32 Exact Partial Producer Tree c16 Contract

This is the smallest native `c16` producer-coupled exact reduction slice. It
composes sixteen real `attention_decode_score_multivalue_cluster` producers in
`result_mode="exact_partial"` directly into the existing
`c16/r2/l8/b59` ordered banked exact finalized tree.

## Scope

- Each external command carries an explicit `head_id`.
- The wrapper broadcasts that command to all sixteen producers. It does not
  infer head identity from tile IDs, wave IDs, or any other proxy.
- Each producer keeps its own score-block input stream and value-block service
  interface.
- The top-level producer interfaces are packed per-producer buses, but each
  producer still preserves the full exact-partial leaf protocol:
  `command_id`, `head_id`, signed `global_max`, unsigned `exp_sum`, `slice`,
  `last`, and `8 x S41` numerators (`328` payload bits).
- The wrapper feeds those sixteen producer leaves directly into the existing
  `c16/r2/l8/b59` ordered banked exact finalized tree without functional hash
  shortcuts in RTL.

## Explicit Non-Claims

- `llama_tile_cadence_unclosed = true`.
- No claim is made that `16 clusters x 8 tile waves x 986 cycles` has been
  mapped or closed.
- No NoC closure is claimed for the direct `328`-bit exact-partial links.
- No SRAM placement or PPA closure is claimed for this wrapper.
- No full `heads=32` native RTL simulation claim is recorded here; the checked-in
  probe stays at `1-2` heads to keep CI tractable.

## Workload Assumptions

- The checked-in probe workload uses `3` score blocks per head.
- Each block carries `3` score beats into each producer `m1x8` cluster input
  stream.
- Heads run in explicit in-order command sequence.
- The coupled slice preserves ready/valid backpressure equivalence end to end:
  producer egress -> `c16` tree -> ordered banked finalizer -> finalized root
  stream.

## Root Timing Boundary

- The reused banked finalized tree still inherits the iterative divider timing:
  - divide iterations per group: `57`
  - earliest output latency per banked beat: `58` cycles
  - earliest re-accept interval per banked beat: `59` cycles
- `59` banks remains the first wrap-free lane-8 point.

## Comparison Baseline

- The overlap benefit comparison is not producer serialization.
- The checked-in bound is `producer_parallel_then_reducer_staged`:
  1. run all sixteen standalone producers from cycle `0`
  2. wait until all producer phases have drained
  3. start a standalone `c16/r2/l8/b59` reducer/finalizer phase at that origin
- A fully serialized `producer_fully_serialized_then_reducer_staged` number may
  still be reported as diagnostic context only. It is not used for overlap
  benefit.

## Recorded Native Evidence

- Probe:
  `python npu/eval/probe_attention_score32_exact_partial_producer_tree_c16.py --config runs/designs/npu_blocks/attention_score32_exact_partial_producer_tree_c16_r2_l8_b59/config.json --json`
- Date recorded: July 28, 2026
- Checked-in timing point:
  - heads: `2`
  - finalized outputs: `32`
  - exact finalized hash:
    `69cab7d0a005e21a6a87562b2073dbf0ad358dfe2c72931340a8dc727b564e70`
  - integrated first output cycle: `423`
  - integrated last output cycle: `822`
  - integrated drain cycles: `824`
  - producer partial windows: `343-361 -> 752` first/last across the sixteen
    producers
  - tree dispatch stalls: `0`
  - producer-parallel phase drain cycles: `761`
  - staged reducer first output cycle: `823`
  - staged reducer last output cycle: `854`
  - producer-parallel-then-reducer bound cycles: `855`
  - overlap savings versus producer-parallel-then-reducer: `31` cycles
  - fully serialized diagnostic drain cycles: `11996`

- Smallest smoke/backpressure point:
  - heads: `1`
  - exact finalized hash:
    `d0aed81a674f7052a2fc6b1fa10fdc402d13210886180602656eae0430e4d4a3`
  - integrated drain cycles: `448`

These numbers are bounded native c16 overlap evidence only. They are not a
full-array cadence, NoC, SRAM, or PPA closure claim.
