## Summary
- item_id: `l2_decoder_attention_two_pass_stream_iterdiv_rtl_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_two_pass_stream_iterdiv_rtl_equivalence_llama7b_v1_run_1f217b64ac11a117`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_two_pass_stream_iterdiv_rtl_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_two_pass_stream_iterdiv_rtl_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `d34ba91f06cc149de6ab71b5bd5f783586c629c4`
- review_metadata_source_commit: `d34ba91f06cc149de6ab71b5bd5f783586c629c4`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_two_pass_stream_iterdiv_equivalence`
- comparison_role: `timing_repair_equivalence_gate`
- expected_direction: `prove_exact_iterative_divider_replacement`
- expected_reason: `The replacement must preserve every final value bit and ready/valid schedule before physical promotion.`
- expectation_status: `unspecified`
- evaluation_summary: `Two-pass external-memory stream equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_stream_equivalence__l2_decoder_attention_two_pass_stream_iterdiv_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_stream_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; score_storage=external_ready_valid_sram; kv_replay=external_ready_valid_stream; block_counts=[4, 8]; div_lanes_per_cycle=[1]; scenarios=['always_ready', 'memory_stalls', 'result_backpressure'].`

## Focused Comparison
- primary_question: `Can one-pass online composition remain within a 0.01 output-value error bound across long-context score distributions, or should the scalable RTL use exact two-pass global-max score replay?`
- comparison_role: `timing_repair_equivalence_gate`
- proposal_outcome: `attention_two_pass_stream_equivalence_pass`
- comparison_summary: `Two-pass external-memory stream equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_two_pass_stream_equivalence__l2_decoder_attention_two_pass_stream_iterdiv_rtl_equivalence_llama7b_v1.json: decision=attention_two_pass_stream_equivalence_pass; equivalence_pass=True; semantic_profile=q8_k8_v8_a32_s32_exp_lut_b20_zero_tail_two_pass_global_max; score_storage=external_ready_valid_sram; kv_replay=external_ready_valid_stream; block_counts=[4, 8]; div_lanes_per_cycle=[1]; scenarios=['always_ready', 'memory_stalls', 'result_backpressure'].`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
