# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1`

## Evaluations Consumed
- item: `l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1`
- run: `l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_llama7b_v1_run_c8741aed35a796c1`
- source commit: `a4846f80f6d8eeb052c209d3de8ea3ae0d78ef97`

## Baseline Comparison
- source subtile item: `l2_decoder_attention_kv_subtile_pipeline_schedule_softmax_recip_lut_llama7b_v1`
- fastest schedule: `dual_mac`, `1575.373891 us`
- physically feasible schedule: `split_mac`, `2042.378179 us`

## Result
- decision: `dual_stream_area_blocked`
- best requested mode: `dual_mac`
- best requested latency: `1575.373891 us`
- best requested area fit: `false`
- best requested logic slack: `-397947652.4116 um2`
- compute area over budget: `397947652.4116 um2`
- required compute density gain: `2.008939`
- compute area required by dual-MAC: `792369540.0 um2`
- best feasible mode: `split_mac`
- best feasible latency: `2042.378179 us`
- best feasible logic slack: `467779.32 um2`

## Failures and Caveats
- This is a budget-aware analytic check, not a full placed dual-stream RTL PPA run.
- The online-correction numerical behavior is still inherited from the schedule model.
- Recovering the `1575 us` point requires denser compute or fewer replicas.

## Recommendation
- `iterate`
- reason: Do not treat the dual-MAC subtile point as the physical frontier; it is about `398M um2` over budget. Use split-MAC at `2042.378179 us` as the current physically valid frontier.
- next_action: Evaluate denser fused/int8 compute or reduced-replica schedules if recovering dual-MAC remains important.
