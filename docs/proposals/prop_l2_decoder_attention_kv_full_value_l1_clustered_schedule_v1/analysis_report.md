# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- `candidate_id`: `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`

## Evaluations Consumed
- `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1_run_16edc0bc7856eeb0`
- source commit: `033e6bae8f8f8dbe24b30c26cd2636cdc348fcf6`
- review: PR #731

## Baseline Comparison
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_kv_measured_l1_clustered_schedule_v1__l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- baseline_item_id: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- outcome: `small_latency_regression_frontier_preserved`
- summary: Full-value L1 costs preserve the 1200 mm2/nm64_flat/8-cluster cluster_tree frontier, but add a small latency regression: 15133.019664 -> 15134.080960 us (+1.061296 us, +0.0070%). Measured L1 overhead rises 440292.3894 -> 1233170.5734 um2 and compute replicas drop 265 -> 264.

## Result
- result: `iterate`
- confidence level: merged accepted evidence
- estimated optimization room: pending follow-on comparison
- architecture conclusion robustness: staged evidence
- summary: Full-value L1 costs preserve the 1200 mm2/nm64_flat/8-cluster cluster_tree frontier, but add a small latency regression: 15133.019664 -> 15134.080960 us (+1.061296 us, +0.0070%). Measured L1 overhead rises 440292.3894 -> 1233170.5734 um2 and compute replicas drop 265 -> 264.

## Failures and Caveats
- no additional caveats recorded during automatic finalization

## Recommendation
- `iterate`
- reason: Full-value L1 costs preserve the 1200 mm2/nm64_flat/8-cluster cluster_tree frontier, but add a small latency regression: 15133.019664 -> 15134.080960 us (+1.061296 us, +0.0070%). Measured L1 overhead rises 440292.3894 -> 1233170.5734 um2 and compute replicas drop 265 -> 264.
- next_action: inspect follow-on work after l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1
