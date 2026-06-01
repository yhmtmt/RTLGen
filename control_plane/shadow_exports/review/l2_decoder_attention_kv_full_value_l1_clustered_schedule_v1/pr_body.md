## Summary
- item_id: `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- run_key: `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1_run_16edc0bc7856eeb0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `033e6bae8f8f8dbe24b30c26cd2636cdc348fcf6`
- review_metadata_source_commit: `033e6bae8f8f8dbe24b30c26cd2636cdc348fcf6`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- abstraction_layer: `decoder_attention_kv_full_value_l1_clustered_schedule`
- comparison_role: `candidate`
- expected_direction: `iterate`
- expected_reason: `Use the full-value measured-L1 schedule frontier to choose the next concrete attention memory/NoC integration point.`
- expectation_status: `consistent_with_iterate`
- evaluation_summary: `Full-value L1 costs preserve the 1200 mm2/nm64_flat/8-cluster cluster_tree frontier, but add a small latency regression: 15133.019664 -> 15134.080960 us (+1.061296 us, +0.0070%). Measured L1 overhead rises 440292.3894 -> 1233170.5734 um2 and compute replicas drop 265 -> 264.`

## Focused Comparison
- primary_question: `Does the L2 Llama7B 131k clustered attention frontier selected with folded L1 proxy costs hold after charging the measured full-value L1 tile datapath PPA?`
- comparison_role: `candidate`
- proposal_outcome: `small_latency_regression_frontier_preserved`
- comparison_summary: `Full-value L1 costs preserve the 1200 mm2/nm64_flat/8-cluster cluster_tree frontier, but add a small latency regression: 15133.019664 -> 15134.080960 us (+1.061296 us, +0.0070%). Measured L1 overhead rises 440292.3894 -> 1233170.5734 um2 and compute replicas drop 265 -> 264.`
- baseline_item_id: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- baseline_profile: `hd64_kv4_p8_ppc2_noc128`
- candidate_profile: `hd64_kv8_full_value_p8_ppc2_noc128`
- latency_delta_us: `15133.019664` -> `15134.08096` (`+1.061296` us, `+0.0070%`)
- measured_l1_overhead_area_um2: `440292.3894` -> `1233170.5734` (`+792878.1840`)
- compute_replica_count: `265` -> `264`
- cluster_count/reduction: `8/cluster_tree` -> `8/cluster_tree`

## Checklist
- [x] Commit lightweight campaign artifacts only
- [x] Include metrics row references in result.metrics_rows
- [x] Keep committed result_path fields repo-portable
- [x] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
