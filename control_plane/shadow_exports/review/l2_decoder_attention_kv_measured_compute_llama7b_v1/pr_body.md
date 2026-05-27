## Summary
- item_id: `l2_decoder_attention_kv_measured_compute_llama7b_v1`
- run_key: `l2_decoder_attention_kv_measured_compute_llama7b_v1_run_5581bd21f0fcf794`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_measured_compute_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_measured_compute_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_measured_compute_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_measured_compute_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `f81a2e4f34c1b5dfe3535e3407ae63a2ad875947`
- review_metadata_source_commit: `f81a2e4f34c1b5dfe3535e3407ae63a2ad875947`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_measured_compute`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `If measured compute makes the frontier compute-bound, schedule hierarchical/tiled compute and dispatcher/NoC work; if it remains HBM-bound, continue memory hierarchy/HBM service refinement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_compute__l2_decoder_attention_kv_measured_compute_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `For quality-backed native-GQA KV8 at 131k context, which measured nm1..nm64 compute block and replica budget is feasible under practical die-area splits, and does the selected point remain memory-bound?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_compute__l2_decoder_attention_kv_measured_compute_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
