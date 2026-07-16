# Analysis Report

## Candidate
- `proposal_id`: `prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- `candidate_id`: `l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1`

## Evaluations Consumed
- `l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1`
- `l1_decoder_attention_decode_score_multivalue_cluster_pnr_v1_run_6999bb7c1b6aba41`
- source commit: `40fd671e19b79660e28ecf99ab07f38043e0e937`
- review: PR #1334

## Baseline Comparison
- outcome: `partial_sweep_measured_points`
- summary: The run terminated after capturing status=ok physical rows. Retain only those rows as measured evidence; the sweep is incomplete and unmeasured points must not be inferred as feasible.

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
- reason: Accepted Layer 1 physical metrics were merged in PR #1334 for the current candidate.
- next_action: inspect the next dependent item
