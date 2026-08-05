# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_score32_local_temporal_reducer_gqa8_v1`
- `candidate_id`: `l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_macro_ppa_v1`

## Evaluations Consumed
- `l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_macro_ppa_v1`
- `l1_decoder_attention_score32_local_temporal_reducer_gqa8_factored_hier_folded_mersenne_macro_ppa_v1_run_189c634d2b3ca788`
- source commit: `e796b6f6946d5f76257bcd8c30bc06fedf58d390`
- review: PR #1538

## Baseline Comparison
- outcome: `boundary_no_feasible_points`
- summary: All current Layer 1 metrics rows are non-ok; this is accepted as frontier boundary evidence, not a promotable design point.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: No status=ok Layer 1 rows were produced; non-ok metrics rows are recorded as explicit boundary evidence.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Accepted Layer 1 evidence merged, but no concrete promotion proposal entries were present.
- next_action: inspect the next dependent item
