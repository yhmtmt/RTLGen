## Summary
- item_id: `l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1_run_4bbe2652b40b0ff5`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `0bf76729d525e08aab8b8428ba2c4bb272c48aa5`
- review_metadata_source_commit: `0bf76729d525e08aab8b8428ba2c4bb272c48aa5`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_composed_datapath_physical_feasibility`
- comparison_role: `frontier_closure`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1.json: decision=dual_stream_area_blocked; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`

## Focused Comparison
- primary_question: `After the q12/PWL composed dual-stream wrapper PPA is measured, what Llama7B attention latency, area, energy, and precision-risk point does it produce under the same subtile schedule?`
- comparison_role: `frontier_closure`
- proposal_outcome: `dual_stream_area_blocked`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_q12_pwl_softmax_frontier_llama7b_v1.json: decision=dual_stream_area_blocked; recommended_next_step=measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
