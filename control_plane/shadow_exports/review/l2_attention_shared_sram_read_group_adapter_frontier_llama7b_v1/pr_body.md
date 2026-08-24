## Summary
- item_id: `l2_attention_shared_sram_read_group_adapter_frontier_llama7b_v1`
- run_key: `l2_attention_shared_sram_read_group_adapter_frontier_llama7b_v1_run_8b9937d9e26848c5`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_attention_shared_sram_read_group_adapter_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_attention_shared_sram_read_group_adapter_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_attention_shared_sram_read_group_adapter_frontier_v1`
- proposal_path: `docs/proposals/prop_l2_attention_shared_sram_read_group_adapter_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_attention_shared_sram_read_group_adapter_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `59a047f1a947437b0378b4d9cda79e0244131880`
- review_metadata_source_commit: `719cdfecd7213cf92d54cf7620428ff7c3214de3`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_shared_sram_read_group_adapter_frontier`
- comparison_role: `shared_sram_adapter_exact_service_frontier`
- expected_direction: `record_exact_adapter_service_frontier`
- expected_reason: `Replace width and slot assumptions with exact RTL cycles and common-clock PPA without claiming system token throughput.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_sram_profile__shared_sram_read_group_adapter_frontier__l2_attention_shared_sram_read_group_adapter_frontier_llama7b_v1.json: decision=adapter_frontier_measured_exact; recommended_next_step=compose the selected adapter with measured scheduler, endpoint, NoC, and SRAM macro service.`

## Focused Comparison
- primary_question: `Which embodied adapter width and slot count best serves the shared-SRAM read path before scheduler, endpoint, NoC, and macro costs are composed?`
- comparison_role: `shared_sram_adapter_exact_service_frontier`
- proposal_outcome: `adapter_frontier_measured_exact`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_sram_profile__shared_sram_read_group_adapter_frontier__l2_attention_shared_sram_read_group_adapter_frontier_llama7b_v1.json: decision=adapter_frontier_measured_exact; recommended_next_step=compose the selected adapter with measured scheduler, endpoint, NoC, and SRAM macro service.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
