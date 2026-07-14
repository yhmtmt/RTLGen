## Summary
- item_id: `l2_decoder_attention_operational_dense_tile_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_operational_dense_tile_equivalence_llama7b_v1_run_c800ccde0a40caa8`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_operational_dense_tile_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_operational_dense_tile_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `875614d6bd207082d81f1cef2a27e8ccfcaee746`
- review_metadata_source_commit: `875614d6bd207082d81f1cef2a27e8ccfcaee746`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_operational_dense_tile_equivalence`
- comparison_role: `operational_compute_semantic_gate`
- expected_direction: `prove_operational_dense_tile_equivalence`
- expected_reason: `Do not scale the narrow hash harness as an operational producer.`
- expectation_status: `unspecified`
- evaluation_summary: `RTL component/reference equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_operational_dense_tile_equivalence__l2_decoder_attention_operational_dense_tile_equivalence_llama7b_v1.json: decision=operational_dense_gemm_tile_int8_16x8_equivalence_pass; component=operational_dense_gemm_tile_int8_16x8; semantic_profile=operational_dense_gemm_outer_product_stream_s8_s8_acc32; reference=python_signed_outer_product_gemm; equivalence_pass=True; passed_test_count=2; test_target=tests/test_dense_gemm_tile_stream.py.`

## Focused Comparison
- primary_question: `How far do operational accumulator state, banked SRAM wiring, divider sharing, and local cluster routing move the measured Llama7B throughput, energy, and area frontier?`
- comparison_role: `operational_compute_semantic_gate`
- proposal_outcome: `operational_dense_gemm_tile_int8_16x8_equivalence_pass`
- comparison_summary: `RTL component/reference equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_operational_dense_tile_equivalence__l2_decoder_attention_operational_dense_tile_equivalence_llama7b_v1.json: decision=operational_dense_gemm_tile_int8_16x8_equivalence_pass; component=operational_dense_gemm_tile_int8_16x8; semantic_profile=operational_dense_gemm_outer_product_stream_s8_s8_acc32; reference=python_signed_outer_product_gemm; equivalence_pass=True; passed_test_count=2; test_target=tests/test_dense_gemm_tile_stream.py.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
