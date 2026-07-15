## Summary
- item_id: `l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1_run_1bca3164fbf8efd6`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `13c88a6db52d31d10ba6cb0b057c4750d2277448`
- review_metadata_source_commit: `13c88a6db52d31d10ba6cb0b057c4750d2277448`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_decode_score_tile_equivalence`
- comparison_role: `decode_score_compute_semantic_gate`
- expected_direction: `unknown`
- expectation_status: `unspecified`
- evaluation_summary: `RTL component/reference equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_tile_equivalence__l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1.json: decision=attention_decode_score_tile_int8_1x8_equivalence_pass; component=attention_decode_score_tile_int8_1x8; semantic_profile=llama_decode_qk_score_row_m1_n8_s8_s8_acc32; reference=python_signed_m1_n8_dot_products; equivalence_pass=True; passed_test_count=1; test_target=tests/test_dense_gemm_tile_stream.py::test_packed_decode_score_tile_matches_reference_and_protocol.`

## Focused Comparison
- primary_question: `How do scalar-drain and packed-row M1x8 score tiles change measured area, delay, and the precision-aligned Llama7B token frontier relative to the semantically mismatched M16x8 recost?`
- comparison_role: `decode_score_compute_semantic_gate`
- proposal_outcome: `attention_decode_score_tile_int8_1x8_equivalence_pass`
- comparison_summary: `RTL component/reference equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_tile_equivalence__l2_decoder_attention_decode_score_tile_m1x8_equivalence_llama7b_v1.json: decision=attention_decode_score_tile_int8_1x8_equivalence_pass; component=attention_decode_score_tile_int8_1x8; semantic_profile=llama_decode_qk_score_row_m1_n8_s8_s8_acc32; reference=python_signed_m1_n8_dot_products; equivalence_pass=True; passed_test_count=1; test_target=tests/test_dense_gemm_tile_stream.py::test_packed_decode_score_tile_matches_reference_and_protocol.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
