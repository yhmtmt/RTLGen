## Summary
- item_id: `l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2`
- run_key: `l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2_run_7c0f7950e21a3075`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_spill_scheduler_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `097bbae0734affd6d8b02af787bc2d71180f27dd`
- review_metadata_source_commit: `097bbae0734affd6d8b02af787bc2d71180f27dd`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_spill_scheduler`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use compact tile-level spill scheduling to choose the next concrete memory/NoC RTL or controller measurement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_spill_scheduler__l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `How much of the llama7b_proxy 131k spill latency can be hidden by tile-level prefetch scheduling and finite HBM parallelism?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_spill_scheduler__l2_decoder_attention_kv_spill_scheduler_llama7b_v1_r2.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
