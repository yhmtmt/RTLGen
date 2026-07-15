# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- `candidate_id`: `l1_decoder_attention_decode_score_tile_m1x8_ppa_v1`

## Evaluations Consumed
- `l1_decoder_attention_decode_score_tile_m1x8_ppa_v1`
- `l1_decoder_attention_decode_score_tile_m1x8_ppa_v1_run_ceec4b1c3e107057`
- source commit: `26d98127bae70b4660666b6a7fd284bd8ba117e2`
- review: PR #1303

## Baseline Comparison
- not applicable

## Result
- result: `promote`
- confidence level: merged accepted evidence
- estimated optimization room: accepted at current stage
- architecture conclusion robustness: accepted for the current proposal scope
- summary: Physical metrics recorded from a completed, timing-feasible Layer 1 row.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `promote`
- reason: Accepted Layer 1 physical metrics were merged in PR #1303 for the current candidate.
- next_action: queue l1_decoder_attention_decode_score_local_cluster_pnr_v1
