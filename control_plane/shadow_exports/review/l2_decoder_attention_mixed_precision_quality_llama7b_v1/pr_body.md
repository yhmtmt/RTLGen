## Summary
- item_id: `l2_decoder_attention_mixed_precision_quality_llama7b_v1`
- run_key: `l2_decoder_attention_mixed_precision_quality_llama7b_v1_run_b48421fdaf63879b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_mixed_precision_quality_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_mixed_precision_quality_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_mixed_precision_quality_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_mixed_precision_quality_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_mixed_precision_quality_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `6f0e2290ce508c9a8a90fdbb188ca3843dce173d`
- review_metadata_source_commit: `6f0e2290ce508c9a8a90fdbb188ca3843dce173d`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_mixed_precision_quality`
- comparison_role: `frontier_closure`
- expected_direction: `iterate`
- expected_reason: `Use the proxy-passing mixed-precision candidates to decide the next attention compute PPA target and the required follow-up model-quality gate.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json: decision=mixed_precision_quality_candidate_found; best_quality_candidate=q8_k8_v8_a24_s24_w16; best_quality_decision=mixed_precision_proxy_pass; best_low_cost_candidate=q8_k8_v6_a24_s24_w16; best_low_cost_decision=mixed_precision_proxy_pass; passing_candidate_count=3; borderline_candidate_count=1; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion.`

## Focused Comparison
- primary_question: `Which mixed-precision attention arithmetic candidates are safe enough to become the next RTL/PPA target for the Llama7B frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `mixed_precision_quality_candidate_found`
- comparison_summary: `Decoder attention mixed-precision quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_mixed_precision_quality__l2_decoder_attention_mixed_precision_quality_llama7b_v1.json: decision=mixed_precision_quality_candidate_found; best_quality_candidate=q8_k8_v8_a24_s24_w16; best_quality_decision=mixed_precision_proxy_pass; best_low_cost_candidate=q8_k8_v6_a24_s24_w16; best_low_cost_decision=mixed_precision_proxy_pass; passing_candidate_count=3; borderline_candidate_count=1; dual_stream_required_compute_density_gain=2.011289; recommended_next_step=run PPA for the lowest-cost passing mixed-precision attention compute primitive and keep a real-checkpoint Llama-class quality gate before promotion.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
