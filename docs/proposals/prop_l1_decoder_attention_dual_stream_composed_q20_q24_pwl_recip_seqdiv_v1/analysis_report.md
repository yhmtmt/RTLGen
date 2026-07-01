# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_v1`
- `candidate_id`: `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1`

## Evaluations Consumed
- `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1`
- `l1_decoder_attention_dual_stream_composed_q20_q24_pwl_recip_seqdiv_ppa_v1_run_d51696a71badc45f`
- source commit: `78a9417eebf722c68ebe6ace381856125452e8aa`
- review: PR #1098

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
