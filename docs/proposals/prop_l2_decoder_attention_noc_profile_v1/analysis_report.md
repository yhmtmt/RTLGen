# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_noc_profile_v1`
- `candidate_id`: `l2_decoder_attention_noc_profile_v1`

## Evaluations Consumed
- `l2_decoder_attention_noc_profile_v1`
- `l2_decoder_attention_noc_profile_v1_run_61ae932db739ec43`
- source commit: `254c9db5558254c93ed9e4983b3206693123c766`
- review: PR #736

## Baseline Comparison
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1__l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- baseline_item_id: `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- outcome: `no_measurable_change`
- summary: Focused comparison matched the baseline with no measurable latency or energy delta.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Focused comparison matched the baseline with no measurable latency or energy delta.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Focused comparison matched the baseline with no measurable latency or energy delta.
- next_action: inspect follow-on work after l2_decoder_attention_noc_profile_v1
