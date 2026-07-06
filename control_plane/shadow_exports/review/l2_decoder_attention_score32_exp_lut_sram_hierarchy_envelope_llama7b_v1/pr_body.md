## Summary
- item_id: `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`
- run_key: `l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1_run_3527a58e1b41c4e9`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b759c0945ffb23a9f331b41e5d4d714cb58eb9c5`
- review_metadata_source_commit: `b759c0945ffb23a9f331b41e5d4d714cb58eb9c5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exp_lut_sram_hierarchy_envelope`
- comparison_role: `score32_exp_lut_sram_hierarchy_envelope_audit`
- expected_direction: `record_score32_sram_hierarchy_envelope`
- expected_reason: `The result should bound shared-SRAM capacity and HBM-share sensitivity under explicit macro placement efficiency before choosing the next frontier abstraction.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_stable; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=47.8125; nominal_hbm_byte_share=0.988327026; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=35.046875; conservative_hbm_byte_share=0.991443634; conservative_hbm_share_delta=0.008045196; conservative_projected_latency_us_hbm_share_scaled=12621.763263; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.`

## Focused Comparison
- primary_question: `Does a physically constrained SRAM macro placement envelope materially change the score32 exp-LUT frontier latency/HBM-share conclusion?`
- comparison_role: `score32_exp_lut_sram_hierarchy_envelope_audit`
- proposal_outcome: `score32_exp_lut_sram_hierarchy_envelope_stable`
- comparison_summary: `Decoder score32 exp-LUT SRAM hierarchy envelope evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_sram_hierarchy_envelope__l2_decoder_attention_score32_exp_lut_sram_hierarchy_envelope_llama7b_v1.json: decision=score32_exp_lut_sram_hierarchy_envelope_stable; score32_supported=True; source_score32_latency_us=12519.342352; source_hbm_byte_share=0.983398438; nominal_efficiency=0.75; nominal_shared_sram_capacity_mib=47.8125; nominal_hbm_byte_share=0.988327026; conservative_efficiency=0.55; conservative_shared_sram_capacity_mib=35.046875; conservative_hbm_byte_share=0.991443634; conservative_hbm_share_delta=0.008045196; conservative_projected_latency_us_hbm_share_scaled=12621.763263; remaining_abstractions=['hbm_dram_service', 'sram_macro_floorplan_pnr']; requires_hbm_dram_closure=True.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
