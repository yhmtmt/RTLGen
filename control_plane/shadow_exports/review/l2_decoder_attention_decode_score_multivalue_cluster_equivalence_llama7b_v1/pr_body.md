## Summary
- item_id: `l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1_run_437953cdf5316d7f`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_multivalue_cluster_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `2fddedef260a26ff99e2c51a5ffa65ff8b1f4939`
- review_metadata_source_commit: `2fddedef260a26ff99e2c51a5ffa65ff8b1f4939`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_decode_score_multivalue_cluster_equivalence`
- comparison_role: `shared_score_multivalue_cluster_semantic_gate`
- expected_direction: `prove_shared_score_multivalue_cluster_equivalence`
- expected_reason: `PPA is ineligible until sharing, replay ordering, all 128 output dimensions, and backpressure match the integer model.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score multivalue-cluster equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_cluster_equivalence__l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1.json: decision=decode_score_multivalue_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=decode_m1x8_shared_score_16x8d_value_iterdiv_v1; scenario_count=5; score_tensor_hash=dcdf04e9e1981a3447a532037c35bc10afc81c339014d09fc9bc039578c34387; final_tensor_hash=fbbbe51bfe1d4ebf5f9910fdfdbf7e5eb322fe7633c9d523ac5a3587545cd457; value_slices=16; value_dimensions=128; score_passes_per_command=1; score_writes_per_block=1; score_reads_per_block=1; result_beats_per_command=16.`

## Focused Comparison
- primary_question: `How much of the local-cluster frontier loss comes from repeating score fill and store 16 times instead of filling once and replaying 16 eight-dimensional value slices from shared score state?`
- comparison_role: `shared_score_multivalue_cluster_semantic_gate`
- proposal_outcome: `decode_score_multivalue_cluster_equivalence_pass`
- comparison_summary: `Decoder score multivalue-cluster equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_cluster_equivalence__l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1.json: decision=decode_score_multivalue_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=decode_m1x8_shared_score_16x8d_value_iterdiv_v1; scenario_count=5; score_tensor_hash=dcdf04e9e1981a3447a532037c35bc10afc81c339014d09fc9bc039578c34387; final_tensor_hash=fbbbe51bfe1d4ebf5f9910fdfdbf7e5eb322fe7633c9d523ac5a3587545cd457; value_slices=16; value_dimensions=128; score_passes_per_command=1; score_writes_per_block=1; score_reads_per_block=1; result_beats_per_command=16.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
