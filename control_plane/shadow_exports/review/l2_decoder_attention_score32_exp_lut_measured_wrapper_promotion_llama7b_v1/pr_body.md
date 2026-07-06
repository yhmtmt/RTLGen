## Summary
- item_id: `l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1`
- run_key: `l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1_run_21c02f26440cc217`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `636af107a21652571d024749ce453e11fe576667`
- review_metadata_source_commit: `636af107a21652571d024749ce453e11fe576667`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_score32_exp_lut_measured_wrapper_promotion`
- comparison_role: `score32_exp_lut_wrapper_promotion_audit`
- expected_direction: `close_score32_exp_lut_wrapper_promotion_linkage`
- expected_reason: `The result should report whether the L2 selected wrapper metrics match the merged L1 wrapper PPA and whether partitioned/cluster physical validation is still required.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score32 exp-LUT measured-wrapper promotion evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_measured_wrapper_promotion__l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json: decision=decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded; l2_measured_decision=dual_stream_feasible; l2_candidate_supported=True; l1_wrapper_accepted=True; l1_wrapper_metrics_match=True; l2_selected_wrapper_metrics_csv=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/metrics.csv; recommended_next_step=promote reduced-replica score32 exp-LUT datapath using the measured dual-stream wrapper instead of partitioned-wrapper physical follow-up.; requires_partitioned_or_cluster_validation=False.`

## Focused Comparison
- primary_question: `Is the reduced-replica score32 exp-LUT measured-command-control L2 result directly backed by the measured L1 dual-stream wrapper metrics, or does it still require partitioned/cluster wrapper physical validation?`
- comparison_role: `score32_exp_lut_wrapper_promotion_audit`
- proposal_outcome: `decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded`
- comparison_summary: `Decoder score32 exp-LUT measured-wrapper promotion evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exp_lut_measured_wrapper_promotion__l2_decoder_attention_score32_exp_lut_measured_wrapper_promotion_llama7b_v1.json: decision=decoder_attention_score32_exp_lut_measured_wrapper_promotion_recorded; l2_measured_decision=dual_stream_feasible; l2_candidate_supported=True; l1_wrapper_accepted=True; l1_wrapper_metrics_match=True; l2_selected_wrapper_metrics_csv=runs/designs/npu_blocks/attention_dual_stream_composed_int8_q8k8v8_16x8_p8_ppc2_nohash_score32_w16_exp_lut_div_b20/metrics.csv; recommended_next_step=promote reduced-replica score32 exp-LUT datapath using the measured dual-stream wrapper instead of partitioned-wrapper physical follow-up.; requires_partitioned_or_cluster_validation=False.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
