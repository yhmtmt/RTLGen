## Summary
- item_id: `l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1_run_41bdfaaadc1991b8`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_decode_score_tile_m1x8_llama7b_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `8599a72f2343a9e18e74ad432728bb37526e340f`
- review_metadata_source_commit: `8599a72f2343a9e18e74ad432728bb37526e340f`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_decode_score_local_cluster_equivalence`
- comparison_role: `decode_exact_cluster_semantic_gate`
- expected_direction: `prove_composed_decode_cluster_equivalence`
- expected_reason: `Cluster PPA is ineligible until scaling, score storage, replay ordering, value rendezvous, division, and backpressure preserve the end-to-end integer contract.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder score local-cluster equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_equivalence__l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1.json: decision=decode_score_local_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=decode_m1x8_score_sram_two_pass_iterdiv_v1; scenario_count=4; score_tensor_hash=7b469c9555a690c6f77efe3831df349b0ab2bbe40e6b12c5b6e5559a86fa01b7; final_tensor_hash=b7e5f766ea14f412a24fcec8ec657da6b92ae5d142e75da87501f0444709b515; score_scale_lanes_per_cycle=1.`

## Focused Comparison
- primary_question: `How do scalar-drain and packed-row M1x8 score tiles change measured area, delay, and the precision-aligned Llama7B token frontier relative to the semantically mismatched M16x8 recost?`
- comparison_role: `decode_exact_cluster_semantic_gate`
- proposal_outcome: `decode_score_local_cluster_equivalence_pass`
- comparison_summary: `Decoder score local-cluster equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_local_cluster_equivalence__l2_decoder_attention_decode_score_local_cluster_equivalence_llama7b_v1.json: decision=decode_score_local_cluster_equivalence_pass; equivalence_pass=True; semantic_profile=decode_m1x8_score_sram_two_pass_iterdiv_v1; scenario_count=4; score_tensor_hash=7b469c9555a690c6f77efe3831df349b0ab2bbe40e6b12c5b6e5559a86fa01b7; final_tensor_hash=b7e5f766ea14f412a24fcec8ec657da6b92ae5d142e75da87501f0444709b515; score_scale_lanes_per_cycle=1.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
