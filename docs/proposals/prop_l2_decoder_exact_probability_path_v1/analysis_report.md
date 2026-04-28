# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_exact_probability_path_v1`
- `candidate_id`: `l2_decoder_exact_probability_path_v1`

## Evaluations Consumed
- `l2_decoder_exact_probability_path_v1`
- `l2_decoder_exact_probability_path_v1_run_930a1658a4e342e8`
- source commit: `251d3fddd95a52d4555d670cf3b95bec26a4d0b7`
- review: PR #233

## Baseline Comparison
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_contract_eval_confirm_v1`
- baseline_item_id: `l2_decoder_contract_eval_confirm_v1`
- outcome: `quality_improved`
- summary: Decoder quality improved from 0.8 to 1.0 exact/top-k on 5 samples; campaign physical metrics matched the paired baseline.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Decoder quality improved from 0.8 to 1.0 exact/top-k on 5 samples; campaign physical metrics matched the paired baseline.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Decoder quality improved from 0.8 to 1.0 exact/top-k on 5 samples; campaign physical metrics matched the paired baseline.
- next_action: inspect follow-on work after l2_decoder_exact_probability_path_v1
