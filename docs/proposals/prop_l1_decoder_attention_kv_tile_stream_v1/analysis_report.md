# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_kv_tile_stream_v1`
- `candidate_id`: `l1_decoder_attention_kv_tile_smoke_v1`

## Evaluations Consumed
- `l1_decoder_attention_kv_tile_smoke_v1`
- `l1_decoder_attention_kv_tile_smoke_v1_run_546f61362feb8c90`
- source commit: `4deca89f916e647c2a85f55a955db682792ebf4f`
- review: PR #469

## Baseline Comparison
- not applicable

## Result
- result: `promote`
- confidence level: merged accepted evidence
- estimated optimization room: accepted at current stage
- architecture conclusion robustness: accepted for the current proposal scope
- summary: Physical metrics recorded from an accepted status=ok Layer 1 row.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `promote`
- reason: Accepted Layer 1 physical metrics were merged in PR #469 for the current candidate.
- next_action: queue l1_decoder_attention_kv_tile_frontier_v1
