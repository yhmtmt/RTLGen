## Summary
- item_id: `l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1_run_398e1665ded99f8d`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `c523a854b1765103086dfd3889744d6cfbff0c19`
- review_metadata_source_commit: `c523a854b1765103086dfd3889744d6cfbff0c19`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_physical_hbm_frontier`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use the physical HBM and KV-byte-reduction frontier to choose the next structural KV, SRAM, or HBM-interface refinement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_frontier__l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Under plausible physical HBM stack, pseudo-channel, width, MT/s, and efficiency assumptions, which KV sharing and KV bitwidth choices move llama7B 131k decode away from the HBM wall?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_frontier__l2_decoder_attention_kv_physical_hbm_frontier_llama7b_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
