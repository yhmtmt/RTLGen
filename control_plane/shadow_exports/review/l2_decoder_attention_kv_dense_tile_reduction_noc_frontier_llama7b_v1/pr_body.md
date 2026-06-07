## Summary
- item_id: `l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1_run_73e9aa2c59ca67b3`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `756ad35a9127cf00813a2379cb4abeaf8de1d743`
- review_metadata_source_commit: `756ad35a9127cf00813a2379cb4abeaf8de1d743`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_dense_tile_reduction_noc_frontier`
- comparison_role: `frontier_synthesis`
- expected_direction: `classify_reduction_noc_frontier`
- expected_reason: `The result should rank dense_gemm_16x8_k1_p1 schedule points by SRAM placement, NoC bandwidth/hops, cluster count, and reduction overhead so the next embodied memory/NoC design target is clear.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `For the selected dense tile compute anchor, which local/shared SRAM, cluster count, NoC bandwidth/hop, and reduction-overhead points remain on the Llama7B frontier?`
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
