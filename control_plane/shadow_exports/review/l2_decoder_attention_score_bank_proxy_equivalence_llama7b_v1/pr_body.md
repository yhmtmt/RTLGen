## Summary
- item_id: `l2_decoder_attention_score_bank_proxy_equivalence_llama7b_v1`
- run_key: `l2_decoder_attention_score_bank_proxy_equivalence_llama7b_v1_run_2853d6d96dbd808e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_score_bank_proxy_equivalence_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_score_bank_proxy_equivalence_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `875614d6bd207082d81f1cef2a27e8ccfcaee746`
- review_metadata_source_commit: `875614d6bd207082d81f1cef2a27e8ccfcaee746`

## Evaluation Mode
- evaluation_mode: `equivalence_gate`
- abstraction_layer: `decoder_attention_score_bank_proxy_equivalence`
- comparison_role: `score_memory_semantic_gate`
- expected_direction: `prove_banked_score_memory_equivalence`
- expected_reason: `Do not place an area-only SRAM rectangle without a valid address and data mapping.`
- expectation_status: `unspecified`
- evaluation_summary: `RTL component/reference equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score_bank_proxy_equivalence__l2_decoder_attention_score_bank_proxy_equivalence_llama7b_v1.json: decision=attention_score_bank_proxy_equivalence_pass; component=attention_score_bank_proxy; semantic_profile=synchronous_16kx256_1rw_eight_by_seven_banking; reference=behavioral_synchronous_1rw_memory; equivalence_pass=True; passed_test_count=2; test_target=tests/test_attention_score_bank_proxy.py.`

## Focused Comparison
- primary_question: `How far do operational accumulator state, banked SRAM wiring, divider sharing, and local cluster routing move the measured Llama7B throughput, energy, and area frontier?`
- comparison_role: `score_memory_semantic_gate`
- proposal_outcome: `attention_score_bank_proxy_equivalence_pass`
- comparison_summary: `RTL component/reference equivalence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score_bank_proxy_equivalence__l2_decoder_attention_score_bank_proxy_equivalence_llama7b_v1.json: decision=attention_score_bank_proxy_equivalence_pass; component=attention_score_bank_proxy; semantic_profile=synchronous_16kx256_1rw_eight_by_seven_banking; reference=behavioral_synchronous_1rw_memory; equivalence_pass=True; passed_test_count=2; test_target=tests/test_attention_score_bank_proxy.py.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
