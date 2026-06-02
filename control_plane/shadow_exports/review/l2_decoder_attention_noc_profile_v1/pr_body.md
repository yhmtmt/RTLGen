## Summary
- item_id: `l2_decoder_attention_noc_profile_v1`
- run_key: `l2_decoder_attention_noc_profile_v1_run_61ae932db739ec43`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_noc_profile_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_noc_profile_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_noc_profile_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_noc_profile_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_noc_profile_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `254c9db5558254c93ed9e4983b3206693123c766`
- review_metadata_source_commit: `254c9db5558254c93ed9e4983b3206693123c766`

## Evaluation Mode
- evaluation_mode: `profile_measurement`
- abstraction_layer: `decoder_attention_noc_profile`
- comparison_role: `abstraction_closure`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison matched the baseline with no measurable latency or energy delta.`

## Focused Comparison
- primary_question: `For the selected 512-token, 8-cluster Llama7B attention frontier, what NoC payload bytes, flits, and service-cycle bounds apply under 128/256-bit paths, hop counts, virtual channels, and arbitration efficiencies?`
- comparison_role: `abstraction_closure`
- proposal_outcome: `no_measurable_change`
- comparison_summary: `Focused comparison matched the baseline with no measurable latency or energy delta.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1__l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- baseline_item_id: `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- latency_delta fp16_nm1/flat_nomacro/mlp1: `0.004282` -> `0.004282` ms
- energy_delta fp16_nm1/flat_nomacro/mlp1: `8.26948404e-07` -> `8.26948404e-07` mJ
- latency_delta fp16_nm1/flat_nomacro/mlp2: `0.05353399999999999` -> `0.05353399999999999` ms
- energy_delta fp16_nm1/flat_nomacro/mlp2: `1.0338593148e-05` -> `1.0338593148e-05` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
