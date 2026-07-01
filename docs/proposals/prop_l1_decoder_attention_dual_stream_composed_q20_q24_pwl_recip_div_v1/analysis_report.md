# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_div_v1`
- `candidate_id`: `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_div_ppa_v1_r2`

## Evaluations Consumed
- `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_div_ppa_v1_r2`
- `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_div_ppa_v1_r2_run_cb97d0cbe3e1ac59`
- source commit: `50c3aede78967932d1e7aaf9f8510551bc31b9a3`
- review: PR #1096

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
