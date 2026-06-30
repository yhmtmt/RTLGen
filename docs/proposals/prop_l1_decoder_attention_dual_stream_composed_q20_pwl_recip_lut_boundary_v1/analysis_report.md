# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q20_pwl_recip_lut_boundary_v1`
- `candidate_id`: `l1_decoder_attention_dual_stream_composed_q20_pwl_recip_lut_boundary_ppa_v1`

## Evaluations Consumed
- `l1_decoder_attention_dual_stream_composed_q20_pwl_recip_lut_boundary_ppa_v1`
- `l1_decoder_attention_dual_stream_composed_q20_pwl_recip_lut_boundary_ppa_v1_run_4fc7783b1877ff1b`
- source commit: `91656b74811cb776cfe2d4b546e781c93c0743f7`
- review: PR #1091

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
