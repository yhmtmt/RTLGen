# Score32 Exact Partial Producer Tree Contract

This is the first producer-coupled exact reduction slice. It composes two real
`attention_decode_score_multivalue_cluster` producers in `result_mode="exact_partial"`
directly into the existing `c2/r2/l8/b59` ordered banked exact finalized tree.

## Scope

- Each external command carries an explicit `head_id`.
- The wrapper broadcasts that command to both producers. It does not infer head
  identity from tile IDs, wave IDs, or any other proxy.
- Each producer keeps its own score-block input stream and value-block service
  interface.
- The producer egress is wired losslessly into the tree leaf protocol:
  `command_id`, `head_id`, signed `global_max`, unsigned `exp_sum`, `slice`,
  `last`, and `8 x S41` numerators (`328` payload bits).
- This measures native producer arrival overlap for the `c2` slice only.

## Explicit Non-Claims

- `llama_tile_cadence_unclosed = true`.
- No claim is made that `16 clusters x 8 tile waves x 986 cycles` has been
  mapped or closed.
- No NoC closure is claimed for the direct `328`-bit exact-partial links.
- No SRAM placement or PPA closure is claimed for this wrapper.

## Workload Assumptions

- The checked-in probe workload uses `3` score blocks per head.
- Each block carries `3` score beats into the `m1x8` cluster input stream.
- Heads run in explicit in-order command sequence.
- The coupled slice preserves ready/valid backpressure equivalence end to end:
  producer egress -> c2 tree -> ordered banked finalizer -> finalized root
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
  1. run both standalone producers from cycle `0`
  2. wait until both producer phases have drained
  3. start a standalone `c2/r2/l8/b59` reducer/finalizer phase at that origin
- Cycle origin semantics:
  - producer phase origin: `0`
  - producer phase drain: the larger standalone producer drain count
  - reducer phase origin: producer phase drain
  - reducer service offsets: the standalone `c2/r2/l8/b59` saturated service
    offsets from that reducer origin
- A fully serialized `producer_fully_serialized_then_reducer_staged` number may
  still be reported as diagnostic context only. It is not used for overlap
  benefit.

## Recorded Full Native Evidence

- Probe:
  `python npu/eval/probe_attention_score32_exact_partial_producer_tree.py --config runs/designs/npu_blocks/attention_score32_exact_partial_producer_tree_c2_r2_l8_b59/config_heads32_native.json --json`
- Date recorded: July 28, 2026
- Full native point:
  - heads: `32`
  - finalized outputs: `512`
  - exact finalized hash:
    `f2573d701a6454ed4a4e12334560f2801cd941b33fd416ddea7c0492eacfdadf`
  - integrated first output cycle: `412`
  - integrated last output cycle: `11906`
  - integrated drain cycles: `11908`
  - producer 0 partial window: `325 -> 11840`
  - producer 1 partial window: `353 -> 11840`
  - producer leaf stalls: `[840, 0]`
  - tree dispatch stalls: `0`
  - producer-parallel phase drain cycles: `12052`
  - staged reducer first output cycle: `12111`
  - staged reducer last output cycle: `12622`
  - producer-parallel-then-reducer bound cycles: `12623`
  - overlap savings versus producer-parallel-then-reducer: `715` cycles
  - fully serialized diagnostic drain cycles: `24352`

- Small checked-in CI point:
  - heads: `4`
  - exact finalized hash:
    `3a8ed3d5e27a2667acd74d7191dc5a39a1375e9b17089b2559ef90b93121f19b`
  - integrated drain cycles: `1545`
  - producer-parallel phase drain cycles: `1504`
  - producer-parallel-then-reducer bound cycles: `1627`
  - overlap savings versus producer-parallel-then-reducer: `82` cycles
  - fully serialized diagnostic drain cycles: `3090`

These numbers are timing evidence for the checked-in `c2` native overlap slice.
They are not a full-array cadence claim.
