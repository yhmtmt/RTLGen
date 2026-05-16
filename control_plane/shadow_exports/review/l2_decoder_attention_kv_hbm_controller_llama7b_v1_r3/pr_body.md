## Summary
- item_id: `l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3`
- run_key: `l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3_run_076e4c95d23d9b4d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_hbm_controller_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_hbm_controller_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_hbm_controller_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `19896536fe7b1f600961037e118cb9b73be4c6a3`
- review_metadata_source_commit: `19896536fe7b1f600961037e118cb9b73be4c6a3`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_hbm_controller`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use HBM-controller feasibility to choose the next concrete memory/NoC RTL or HBM prefetch interface measurement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_controller__l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Which HBM channel, burst, outstanding-request, command-overhead, and row-locality assumptions are needed to make the llama7B spill schedule plausible?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_hbm_controller__l2_decoder_attention_kv_hbm_controller_llama7b_v1_r3.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
