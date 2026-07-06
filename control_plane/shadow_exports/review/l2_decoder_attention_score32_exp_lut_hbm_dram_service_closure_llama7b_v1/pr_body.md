## Summary
- item_id: `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`
- run_key: `l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1_run_b4033016c25d2334`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `7270e2c9e95e17b1adb592ca35e4a3e313357dff`
- review_metadata_source_commit: `7270e2c9e95e17b1adb592ca35e4a3e313357dff`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exp_lut_hbm_dram_service_closure`
- comparison_role: `score32_exp_lut_hbm_dram_service_closure_audit`
- expected_direction: `record_score32_hbm_dram_service_closure`
- expected_reason: `Record whether score32-specific HBM/DRAM service latency or calibrated HBM energy changes the current frontier account.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 exp-LUT HBM/DRAM service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_hbm_dram_service_closure__l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json: decision=score32_exp_lut_hbm_dram_service_closure_hbm_sensitive; best_latency_us=12532.357427; best_latency_token_throughput_per_s=79.793447149; best_latency_hbm_energy_mj_per_token=134.280615241; best_energy_hbm_energy_mj_per_token=134.280615241; source_score32_latency_us=12519.342352; source_controller_service_cycles=1301; remaining_abstractions=['cycle_accurate_hbm_controller_rtl', 'hbm_vendor_current_signoff'].`

## Focused Comparison
- primary_question: `Does score32-specific HBM/DRAM service and calibrated HBM energy materially change the current score32 exp-LUT Llama7B frontier account?`
- comparison_role: `score32_exp_lut_hbm_dram_service_closure_audit`
- proposal_outcome: `score32_exp_lut_hbm_dram_service_closure_hbm_sensitive`
- comparison_summary: `Decoder score32 exp-LUT HBM/DRAM service-closure evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_hbm_dram_service_closure__l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json: decision=score32_exp_lut_hbm_dram_service_closure_hbm_sensitive; best_latency_us=12532.357427; best_latency_token_throughput_per_s=79.793447149; best_latency_hbm_energy_mj_per_token=134.280615241; best_energy_hbm_energy_mj_per_token=134.280615241; source_score32_latency_us=12519.342352; source_controller_service_cycles=1301; remaining_abstractions=['cycle_accurate_hbm_controller_rtl', 'hbm_vendor_current_signoff'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
