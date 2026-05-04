# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_logit_rank_streaming_hierarchy_v1`
- `title`: `Decoder logit-rank streaming hierarchy`

## Problem
The rank-only decoder path has evidence for raw-logit bypass and measured
tile-level rank datapaths, but the integration boundary is still implicit. A
full vocabulary reduction needs stable token identity, tile completion, lane
masking, and backpressure semantics before implementation can safely overlap
output projection with rank reduction.

## Hypothesis
A pair of ready/valid streams can carry raw logits into tile rankers and
ranked candidates out to a cross-tile reducer without materializing softmax
probabilities. The contract is sufficient if it defines packet stability,
`tile_id`, `base_token_id`, `lane_valid`, and `last` behavior, and if it
states when upstream producers may overlap subsequent tiles with downstream
ranking.

## Evaluation Scope
- direct comparison set:
  - spec review of `LogitTileStream`
  - spec review of `CandidateStream`
  - overlap and backpressure rule review
  - rough latency/FIFO estimate versus measured flat r8/r16/r32 logit-rank
    datapaths
- evaluation mode:
  - `frontier_detail`
- dependency order:
  - depends on the raw-logit bypass evidence and logit-rank datapath/scale
    measurements
  - requires merged inputs and materialized repo refs
- excluded first-stage comparisons:
  - RTL generation
  - physical synthesis
  - probability-producing decoder modes
- follow-on broad sweep:
  - compare tile width, top-k width, and reducer-depth choices after a narrow
    implementation exists

## Knowledge Inputs
- `docs/proposals/prop_l2_decoder_gpt2_logit_rank_bypass_v1/proposal.json`
- `docs/proposals/prop_l1_decoder_logit_rank_datapath_v1/proposal.json`
- `docs/proposals/prop_l1_decoder_logit_rank_scale_v1/proposal.json`
- `npu/docs/decoder_logit_rank_streaming_hierarchy.md`
- `npu/eval/estimate_llm_decoder_logit_rank_streaming_hierarchy.py`

## Candidate Direction
Define a rank-only hierarchy:

- output projection emits raw logits in fixed-width `LogitTileStream` beats
- per-tile rankers emit bounded `CandidateStream` beats
- a cross-tile reducer consumes candidates and emits greedy or top-k decisions
- probability consumers remain out of scope and must use a probability path

## Direction Gate
- status: pending
- approved_by:
- approved_utc:
- note:
