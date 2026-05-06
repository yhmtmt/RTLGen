# Design Brief

## Proposal

- `proposal_id`: `prop_l1_decoder_logit_rank_wide_scale_v1`
- `title`: `Decoder logit rank wide scaling`

## Problem

The L2 decoder logit-rank streaming sweep now includes producer widths 64 and
128 for larger-vocabulary scale stability, but those width points still rely on
scaled ranker PPA proxies. That makes the current `w64` and `w128` rankings less
trustworthy than the measured row-8, row-16, and row-32 points.

## Hypothesis

Direct row-64 and row-128 measurements will expose whether the wider rank tile
frontier remains useful or whether the architecture should move toward a
hierarchical or pipelined ranker before producer integration.

## Evaluation Scope

Direct comparison set:

- `logit_rank_r64_l16_k1`
- `logit_rank_r64_l16_k4`
- `logit_rank_r128_l16_k1`
- `logit_rank_r128_l16_k4`

Evaluation mode:

- `measurement_only`
- `circuit_block`
- Nangate45 high-utilization L1 sweep

Dependency order:

- depends on merged `l1_decoder_logit_rank_scale_v1`
- depends on merged `l2_decoder_logit_rank_streaming_scale_stability_v1`
- requires merged inputs and materialized refs

Excluded first-stage comparisons:

- producer-integrated macro
- full-vocabulary merge tree
- softmax probability generation
- sampler and beam-search variants beyond `top_k=4`
- floating-point logit quantization

Follow-on broad sweep:

- If row-64/row-128 measurements are usable, update the L2 streaming model to
  consume the measured wide-rank PPA and rerun the scale-stability ranking.
- If timing or PPA is poor, evaluate hierarchical or pipelined ranker
  composition instead of continuing to widen the flat scan tile.

## Knowledge Inputs

- `control_plane/shadow_exports/l1_promotions/l1_decoder_logit_rank_scale_v1.json`
- `control_plane/shadow_exports/l2_decisions/l2_decoder_logit_rank_streaming_scale_stability_v1.json`
- `src/rtlgen/rtl_operations.cpp`
- `npu/eval/model_llm_decoder_logit_rank_streaming.py`

## Candidate Direction

Generate four existing `logit_rank` operation configs with `row_elems` set to
64 or 128 and `top_k` set to 1 or 4. Keep the RTL/perf-sim equivalence surface
unchanged by using the existing `logit_rank` operation type and wrapper
generation path.

## Direction Gate

- status: pending
- approved_by:
- approved_utc:
- note:
