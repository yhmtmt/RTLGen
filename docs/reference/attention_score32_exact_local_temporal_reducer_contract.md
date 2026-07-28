# Score32 Exact Local Temporal Reducer Contract

This document defines the bounded Layer 1 contract for the local exact-partial
aggregation block introduced by
`prop_l1_decoder_attention_score32_local_temporal_reducer_v1`.

## Scope

The block accepts `53` or `54` producer exact-partial streams, reduces each
wave through a staged ready/valid exact merge hierarchy, persists the resulting
local aggregate across exactly `8` waves, and only then emits one exact-partial
aggregate stream.

The block is intentionally local and bounded. It does **not** claim:

- global c16 exact-reduction closure
- producer fan-in wiring closure
- NoC/SRAM integration closure
- PPA, throughput, or Llama frontier closure

## Input contract

Each producer stream is an exact-partial ready/valid stream carrying:

- `command_id[15:0]`
- `head_id[4:0]`
- `global_max` signed 32-bit
- `exp_sum[32:0]`
- `slice[3:0]`
- `last`
- `value[327:0]`

The stream is exact-partial only. No local-normalization approximation is
allowed inside this block.

## Reduction contract

- reduction is staged pairwise exact merge
- odd-leaf stages carry one unmatched stream forward unchanged
- the reduction order is structural and deterministic
- `slice` and `last` semantics must remain explicit; no tile or wave inference
  is allowed from metadata

## Temporal contract

- one local root stream is formed per wave
- waves are accumulated by exact merge into persistent local state
- persistence length is fixed at exactly `8` waves
- after the eighth wave completes, the block emits exactly `16` aggregate beats
- emission order remains `slice=0..15`
- the next temporal window begins only after the previous aggregate stream is
  emitted

## Proof contract

The checked-in probe proves each emitted beat against the structured Python
reference from `npu/sim/perf/attention_exact_partial.py` using:

- ideal-service mode
- seeded ready/valid and output-backpressure stress mode

Evaluator artifact linkage should use:

- `proposal_id`: `prop_l1_decoder_attention_score32_local_temporal_reducer_v1`
- `proposal_path`:
  `docs/proposals/prop_l1_decoder_attention_score32_local_temporal_reducer_v1/proposal.json`
