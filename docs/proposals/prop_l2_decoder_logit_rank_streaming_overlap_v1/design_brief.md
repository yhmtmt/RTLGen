# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_logit_rank_streaming_overlap_v1`
- `title`: `Decoder logit-rank streaming overlap and traffic model`

## Problem
The first hierarchy model established the stream contract, but its simple
latency proxy still favored flat row-8 rank scanning. The missing question is
whether hierarchy value appears when output projection, local ranking, global
merge, FIFO depth, and memory traffic are considered together.

## Hypothesis
If the producer emits logit tiles continuously, a streaming rank path can hide
part of rank latency behind projection and avoid full-vocabulary logit
materialization traffic. The model is useful only if it records the exact
stream observables that future RTL must match.

## Evaluation Scope
- compare buffered rank-after-materialization cycles with streaming cycles
- sweep producer lane width, local top-k, producer II, merge II, and FIFO depth
- report candidate FIFO occupancy and capacity validity
- report candidate traffic versus full-logit write/read traffic
- preserve perf-sim/RTL equivalence observables:
  - accepted `LogitTileStream` beat count
  - accepted `CandidateStream` group count
  - producer stall cycles
  - candidate FIFO max occupancy
  - final `last` completion cycle
  - valid-mask and lower-token-id tie-break behavior

## Exclusions
- no RTL implementation in this proposal
- no new physical synthesis
- no probability-producing decoder modes
- no larger-model quality rerun

## Follow-On Gate
The next job after this model should be an L1 candidate-stream merge datapath
measurement. That RTL block should include a reference-model equivalence test
before PPA metrics are used in architecture rankings.
