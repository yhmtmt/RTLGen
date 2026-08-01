# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1`
- `candidate_id`: `l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1`

## Evaluations Consumed
- `l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1`
- `l1_decoder_attention_score32_exact_partial_pair_merge_sharedscale_ppa_v1_run_b17933308cb1b8c4`
- source commit: `23dcda4fc523c0d467e71debdf45136fce6eaede`
- review: PR #1518

## Baseline Comparison
- outcome: `boundary_no_feasible_points`
- summary: All completed physical rows miss their declared clock period; retain them as timing-boundary evidence and do not promote a feasible design point.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: No timing-feasible Layer 1 rows were produced; completed flows that miss their declared clock period are retained as explicit timing-boundary evidence.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Accepted Layer 1 evidence merged, but no concrete promotion proposal entries were present.
- next_action: inspect the next dependent item
