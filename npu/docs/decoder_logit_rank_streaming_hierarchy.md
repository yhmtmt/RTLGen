# Decoder Logit-Rank Streaming Hierarchy

## Purpose
Define the rank-only streaming boundary for decoder output-logit reduction.
This contract covers greedy next-token, top-k, and beam-candidate ordering paths
that rank raw logits directly. It does not cover softmax probabilities,
temperature sampling, top-p sampling, or probability reporting.

## Hierarchy
The intended pipeline is:

1. output projection produces raw logits by vocabulary tile
2. a tile ranker consumes each `LogitTileStream` beat and selects local
   candidates
3. a cross-tile reducer consumes `CandidateStream` beats and selects global
   candidates

The hierarchy is completion-bound at stream level: downstream results for a
sequence are complete only after the accepted beat with `last=1` has drained
through the cross-tile reducer.

## LogitTileStream
`LogitTileStream` carries one fixed-width vocabulary tile per accepted beat.

Fields:

- `valid`: producer asserts when all payload fields are meaningful.
- `ready`: consumer asserts when it can accept the beat.
- `tile_id`: monotonically increasing tile index within the current decoder
  step, starting at zero.
- `base_token_id`: vocabulary token id represented by lane zero.
- `logit[lane]`: signed raw decoder logit for each lane.
- `lane_valid[lane]`: one bit per lane. A lane with `lane_valid=0` is padding
  and must not produce a candidate.
- `last`: asserted on the final tile beat for the decoder step.

Ready/valid rules:

- A beat transfers only on `valid && ready`.
- While `valid=1 && ready=0`, the producer must hold every payload field
  stable, including `tile_id`, `base_token_id`, `logit`, `lane_valid`, and
  `last`.
- The consumer may deassert `ready` on any cycle. This is the only backpressure
  mechanism.
- The producer may deassert `valid` between beats. Gaps do not change tile
  ordering.
- `tile_id` increments by one per accepted beat for a decoder step. It resets
  to zero on the first accepted beat after the prior accepted `last=1` beat.
- `base_token_id` must equal the first token id covered by the tile. For dense
  vocabulary tiling it normally equals `tile_id * lanes`, but consumers must
  use the explicit field rather than recomputing it.
- `lane_valid` may be sparse only on the final tile unless a later sparse
  vocabulary mode explicitly permits holes. Current dense mode requires all
  non-final tiles to have every lane valid.
- `last=1` marks the final tile for the current decoder step. It is legal for
  `last=1` to appear with some invalid lanes.

Token identity:

- Lane `i` maps to `token_id = base_token_id + i` when `lane_valid[i]=1`.
- Invalid lanes have no token identity and must be ignored for ranking.
- If two valid lanes have equal logits, the stable tie-break is lower
  `token_id` first unless a future mode overrides the tie policy explicitly.

## CandidateStream
`CandidateStream` carries ranked local candidates from tile rankers to the
cross-tile reducer.

Fields:

- `valid`: producer asserts when all candidate payload fields are meaningful.
- `ready`: reducer asserts when it can accept the beat.
- `tile_id`: source tile for the candidates in this beat.
- `base_token_id`: source `LogitTileStream` base token for the tile.
- `rank_base`: rank offset of candidate lane zero within the source tile.
- `candidate_token_id[lane]`: token id for each candidate lane.
- `candidate_logit[lane]`: raw logit paired with each candidate token.
- `candidate_valid[lane]`: one bit per candidate lane.
- `last`: asserted on the final candidate beat for the decoder step.

Ready/valid rules:

- A beat transfers only on `valid && ready`.
- While `valid=1 && ready=0`, the tile ranker must hold all candidate payload
  fields stable, including `tile_id`, `base_token_id`, `rank_base`, candidate
  arrays, valid masks, and `last`.
- The reducer may deassert `ready` on any cycle. Tile rankers must either
  buffer accepted input tiles or backpressure their `LogitTileStream` input.
- `tile_id` identifies the source tile. Candidate beats from different tiles
  may arrive out of order only if the reducer advertises out-of-order support.
  The base contract assumes in-order tile completion.
- `base_token_id` repeats the accepted source tile base. It is redundant with
  explicit `candidate_token_id` values in dense mode, but it preserves tile
  provenance for tracing, debug, and future compressed token encodings.
- `rank_base` increments by the candidate beat width for multi-beat tile
  candidate output. A single-beat top-k tile ranker sets `rank_base=0`.
- `candidate_valid=0` marks padding and must not enter global reduction.
- `last=1` marks the final candidate beat for the decoder step, not merely the
  final candidate from a tile.

Candidate semantics:

- For each valid candidate lane, `candidate_token_id` must correspond to a
  valid input lane from the source tile.
- For dense token encoding, each valid `candidate_token_id` must be in the
  half-open range `[base_token_id, base_token_id + logit_lanes)`.
- Candidates within a tile are sorted by descending `candidate_logit`, with the
  lower `candidate_token_id` tie-break.
- The tile ranker must not emit more than the configured local `k` valid
  candidates per tile.
- The cross-tile reducer applies the same descending-logit and lower-token-id
  tie-break globally.

## Backpressure
Backpressure is local and lossless:

- `CandidateStream.ready=0` may stall tile ranker output.
- A stalled tile ranker may continue accepting `LogitTileStream` input only if
  it has bounded buffering for the accepted tiles and their pending
  candidates.
- If that buffering is unavailable or full, the tile ranker must deassert
  `LogitTileStream.ready`.
- The output projection must treat `LogitTileStream.ready=0` as a hard stall
  for the current beat and must keep the payload stable until transfer.
- No stream participant may drop a valid lane or candidate because downstream
  `ready` is low.

The minimum implementation may use one-entry skid buffers on both stream
boundaries. Deeper buffering is an optimization, not a contract requirement.

## Producer Overlap Assumptions
The overlap model assumes the output projection can produce tile `N+1` while
the ranker/reducer are processing candidates derived from tile `N`, subject to
ready/valid backpressure.

Allowed overlap:

- projection of later vocabulary tiles may continue while earlier tile
  candidates are being reduced
- a tile ranker may accept the next tile before emitting all candidates for the
  prior tile only when internal buffering preserves both tile identity and
  payload stability
- the cross-tile reducer may update a running global top-k after each accepted
  candidate beat and does not need to wait for `last=1`

Required assumptions:

- all tiles in a decoder step use the same hidden-state vector and projection
  parameters
- `tile_id` and `base_token_id` are assigned before any overlapping stage can
  reorder or buffer the beat
- a new decoder step must not reuse `tile_id=0` on a shared stream until the
  prior step's `last=1` beat has been accepted, unless a future `step_id`
  field is added
- consumers must not publish the final next-token/top-k result until the
  accepted `CandidateStream` beat with `last=1` has been reduced

## Producer-Integrated Boundary
The intended r64/r128 ranker use is a producer-integrated ready/valid macro,
not a standalone chip with one top-level scalar pin per logit lane. Explicit
macro-boundary experiments that pad die size to satisfy exposed-pin placement
are diagnostic sensitivity checks. They may be reported beside the normal
model, but their padded die area and scalar top-level pin pressure must not be
charged to the main producer-integrated ranker cost.

A producer-integrated implementation still has to preserve the same stream
contract as the perf simulator: accepted beat counts, valid masks, stable
lower-token tie order, FIFO occupancy under backpressure, and final last-beat
completion must match before RTL PPA is used in rankings.

## Integration Notes
This spec intentionally keeps mapper and evaluator changes out of scope. A
follow-on implementation should bind concrete widths for logit lanes, candidate
lanes, local `k`, and buffering depth, then add validation that random
backpressure preserves the same rank result as an unstreamed full-vocabulary
reference.
