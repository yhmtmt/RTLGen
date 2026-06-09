## Summary
- item_id: `l2_decoder_attention_local_sram_capacity_llama7b_v1`
- run_key: `l2_decoder_attention_local_sram_capacity_llama7b_v1_run_2d4c172783f15d4e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_local_sram_capacity_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_local_sram_capacity_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_local_sram_capacity_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_local_sram_capacity_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_local_sram_capacity_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e51e229abbb25947df144d019d8e545e6d85bf05`
- review_metadata_source_commit: `e51e229abbb25947df144d019d8e545e6d85bf05`

## Evaluation Mode
- evaluation_mode: `profile_measurement`
- abstraction_layer: `decoder_attention_local_sram_capacity`
- comparison_role: `frontier_closure`
- expected_direction: `measure_selected_local_sram_capacity_macro_profile`
- expected_reason: `The result should report per-cluster and all-cluster SRAM area/access/energy and budget fit.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`

## Focused Comparison
- primary_question: `How much area and access time does the selected local SRAM capacity pool require when represented as concrete SRAM macro chunks?`
- comparison_role: `frontier_closure`
- proposal_outcome: `improved`
- comparison_summary: `Focused comparison improved latency and/or energy without regressing matched rows.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1__l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1`
- baseline_item_id: `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_llama7b_v1`
- latency_delta fp16_nm1/flat_nomacro/None: `0.144262` -> `0.004282` ms
- energy_delta fp16_nm1/flat_nomacro/None: `2.7860165964e-05` -> `8.26948404e-07` mJ
- latency_delta fp16_nm1/hier_macro/None: `0.144262` -> `0.004282` ms
- energy_delta fp16_nm1/hier_macro/None: `2.8483233542000004e-05` -> `8.45442362e-07` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
