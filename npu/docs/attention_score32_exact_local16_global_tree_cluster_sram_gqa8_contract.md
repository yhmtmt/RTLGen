# Score32 Exact Local16 Global Tree Cluster SRAM GQA8 Contract

This block composes:

- sixteen real compute clusters with the corrected `p54x8 + p53x8` producer partition
- exactly one local SRAM endpoint per cluster
- the existing `c16/r2/l8/b59` finalized exact global tree

## Scope

- flat packed `856` producer query/key inputs at the top boundary
- no external `1712` value request/response lanes at the top boundary
- sixteen external per-cluster HBM-return fill-target/fill-row interfaces
- direct local exact aggregation into the existing finalized global tree root
- packed cluster compute counters plus packed cluster SRAM counters and errors

## Llama7B Score Accumulation

- every query/key score block has `128` signed INT8 dimensions
- a producer must accept exactly `128` query/key beats for each token block
- `input_last` is asserted only on dimension `127`
- the score entering exp/reduction is the signed sum of all `128` products
- a report is valid Llama7B evidence only when it records both
  `head_dimension=128` and `score_accumulation_beats_per_block=128`
- one logical head group therefore accepts `1,048,576` producer beats; all four
  GQA8 head groups accept `4,194,304`

## Fixed Schedule

- internal group-major command cadence is fixed to head bases `0, 8, 16, 24`
- each head base runs waves `0..7`
- reset always returns the cadence tracker to `head_base=0, wave=0`
- command issue is legal only when:
  - `command_head_base` equals the current expected head base
  - all `16` compute clusters are ready
  - all `16` resident SRAM endpoints are ready

## Fill Prefetch Window

- each cluster fill target is accepted only when its `{head_base, wave}` equals:
  - the current expected command, or
  - the immediate group-major successor
- successor progression includes both `wave7 -> next head_base wave0` and `head_base24 -> head_base0`
- valid fill metadata outside that two-command prefetch window latches `fill_schedule_contract_error`
- invalid fill metadata also latches `fill_schedule_contract_error`
- allowed fill targets may hold `valid` while `ready` is low without error; that remains ordinary backpressure
- buffer selection remains deterministic at the cluster endpoint: `buffer_sel == wave[0]`

## Release Invariant

- each cluster endpoint releases its active SRAM command exactly once per accepted wave
- release requires all of the following in the same cycle:
  - every real producer `command_completed_count` equals that cluster's `wave_command_accept_count`
  - `wave_command_accept_count > released_count`
  - endpoint `outstanding_response_occupancy == 0`
- this invariant is guarded in the generated RTL with sticky `sram_release_guard_error`
- backpressure alone is not treated as a release error

## Remaining Abstractions

- external HBM return-fill generation and transport remain outside this block
- external mesh NoC fill transport remains outside this block
- physical PPA closure remains open
