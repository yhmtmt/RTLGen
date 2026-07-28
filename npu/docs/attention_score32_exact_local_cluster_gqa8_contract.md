# Score32 Exact Local Cluster GQA8 Contract

This wrapper is the full-width functional local cluster for the exact score32
GQA8 path. It is intentionally the real p53 or p54 architecture, not a proxy
reduction or hash-only equivalence harness.

## Scope

- `53` or `54` exact partial dual-stream producers
- direct producer leaf wiring into the corrected GQA8 local temporal reducer
- `4` logical head groups with head bases `[0, 8, 16, 24]`
- `8` persistent waves per logical group
- `16` value slices per head
- `512` final exact partial output beats per full run

## Command Contract

- Shared fields `command_id`, `command_head_base`, `command_score_multiplier`,
  and `command_score_shift` are broadcast across the full producer set.
- `command_block_count` is packed as `53 x 15` or `54 x 15` bits, one
  independent unsigned field per producer.
- Command issue is atomic across the cluster:
  - the wrapper may accept a wave command only when every producer is ready;
  - no subset command acceptance is legal.
- Wave commands run group-major:
  - head base `0`, waves `0..7`
  - head base `8`, waves `0..7`
  - head base `16`, waves `0..7`
  - head base `24`, waves `0..7`

## Corrected Rotation Schedule

Each extra producer receives `2` blocks per stream for its logical group. Every
other producer receives `1`.

### P53

- group `0`: producers `0..10`
- group `1`: producers `11..21`
- group `2`: producers `22..32`
- group `3`: producers `33..43`

### P54

- group `0`: producers `0..9`
- group `1`: producers `10..19`
- group `2`: producers `20..29`
- group `3`: producers `30..39`

Every group still covers exactly `64` blocks per stream.

## Interface Contract

- The wrapper exposes independent producer input `valid`, `ready`, `last`,
  `query`, and `key` lanes for every producer.
- The wrapper exposes all `2 x producers` value-memory request and response
  lanes directly at the top level.
- The wrapper does not abstract or synthesize an SRAM or NoC fabric internally.
- Each producer's exact result `valid`, `ready`, `command_id`, `head_id`,
  `global_max`, `exp_sum`, `slice`, `last`, and `value` connects directly and
  index-preserving to the matching reducer leaf input.

## Reference And Probe Contract

- Stimulus must use unique data keyed by producer, group, wave, head, and slice
  so producer permutations cannot pass.
- The structured reference path is:
  - real producer reference per wave
  - staged p53/p54 local merge
  - eight-wave temporal merge
- Comparison is exact per beat and checks both metadata and payload. Hash-only
  equivalence is not sufficient evidence.

## Remaining Abstractions

- `noc_sram_ppa_open`
- `global_c16_exact_reduction_open`

No claim is made here about NoC closure, SRAM macro closure, or global c16
composition.
