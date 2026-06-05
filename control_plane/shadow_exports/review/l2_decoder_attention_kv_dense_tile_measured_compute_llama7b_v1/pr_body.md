## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1_run_e388a4bf91d95b36`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `494cc58c41cdaa3060bb7104f65d0bf88b01d940`
- review_metadata_source_commit: `494cc58c41cdaa3060bb7104f65d0bf88b01d940`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_measured_compute`
- comparison_role: `frontier_synthesis`
- expected_direction: `select_dense_tile_compute_anchor`
- expected_reason: `The job should identify the dense tile shape and die/logic budget frontier after substituting PR #764 measured dense tile PPA into the Llama7B 131k physical-HBM model.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `When dense tile PPA from l1_npu_dense_gemm_tile_scaling_v2 is substituted into the quality-backed native-GQA KV8 Llama7B 131k physical-HBM memory/NoC model, which die and logic budgets become feasible and which dense tile shape is selected?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
