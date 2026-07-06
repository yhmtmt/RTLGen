## Summary
- item_id: `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1`
- run_key: `l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1_run_b3e9867f98ad3184`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `241c0c1b8daef4cf4a59a3c687d67feb5fef28e5`
- review_metadata_source_commit: `241c0c1b8daef4cf4a59a3c687d67feb5fef28e5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exp_lut_service_closure`
- comparison_role: `score32_exp_lut_service_closure_audit`
- expected_direction: `record_score32_exp_lut_service_closure`
- expected_reason: `The result should state whether score32 exp-LUT is supported by measured wrapper evidence and list remaining inherited service abstractions before the next frontier job.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 exp-LUT service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_service_closure__l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json: decision=score32_exp_lut_service_closure_recorded; score32_supported=True; wrapper_metrics_match=True; selected_semantic_profile=score32_exp_lut_div; latency_us=12519.342352; source_latency_us=1575.373891; macs_per_cycle=104320; dominant_tile_resource=pipeline_attention; remaining_abstractions=['tile_local_and_shared_sram', 'hbm_dram_service']; requires_hbm_dram_closure=True.`

## Focused Comparison
- primary_question: `Which service components are measured, measured-estimated, or still inherited for the promoted score32 exp-LUT Llama7B attention row?`
- comparison_role: `score32_exp_lut_service_closure_audit`
- proposal_outcome: `score32_exp_lut_service_closure_recorded`
- comparison_summary: `Decoder score32 exp-LUT service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_service_closure__l2_decoder_attention_score32_exp_lut_service_closure_llama7b_v1.json: decision=score32_exp_lut_service_closure_recorded; score32_supported=True; wrapper_metrics_match=True; selected_semantic_profile=score32_exp_lut_div; latency_us=12519.342352; source_latency_us=1575.373891; macs_per_cycle=104320; dominant_tile_resource=pipeline_attention; remaining_abstractions=['tile_local_and_shared_sram', 'hbm_dram_service']; requires_hbm_dram_closure=True.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
