# Design Brief

## Scope

Add `candidate_stream_merge_fifo` as an RTLGen operation and measure it as a Layer 1 circuit block.

## Interface

The generated module has a `CandidateStream`-style input:

- `in_valid`, `in_ready`, `in_last`
- `in_valid_mask`
- `in_token_ids`
- `in_logits`

The output is held on `out_valid` until `out_ready`, with merged top-k token ids, logits, and valid mask.

## Equivalence Contract

Perf-sim and RTL must agree on accepted group count, stall cycles, FIFO maximum occupancy, final completion cycle, output valid mask, and top-k ordering. Exact logit ties choose the lower token id.

## Follow-On

After L1 PPA merges, bind the measured area/timing/power back into the decoder streaming overlap model and decide whether to keep register FIFO, try SRAM-backed FIFO, or broaden producer widths.
