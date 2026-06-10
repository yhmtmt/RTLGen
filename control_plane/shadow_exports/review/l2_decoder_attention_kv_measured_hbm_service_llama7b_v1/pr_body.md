## Summary
- item_id: `l2_decoder_attention_kv_measured_hbm_service_llama7b_v1`
- run_key: `l2_decoder_attention_kv_measured_hbm_service_llama7b_v1_run_a0e826ab4b392a54`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_measured_hbm_service_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_measured_hbm_service_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_measured_hbm_service_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_measured_hbm_service_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_measured_hbm_service_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `5a426fc6db310aea694834210d26be2d4109d584`
- review_metadata_source_commit: `5a426fc6db310aea694834210d26be2d4109d584`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_measured_hbm_service`
- comparison_role: `frontier_closure`
- expected_direction: `record_measured_hbm_service_frontier`
- expected_reason: `The result should report best latency, effective HBM bytes/cycle, source-vs-derived HBM efficiency, controller service cycles, and dominant resource.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder measured-HBM service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_llama7b_v1.json: decision=measured_hbm_service_recorded; latency_us=2138.84136; dominant_tile_resource=tile_attention; effective_hbm_bytes_per_cycle=792.596465; source_effective_hbm_bytes_per_cycle=41341.3632; derived_hbm_efficiency_vs_source=0.019172; controller_service_cycles=1301; tile_attention_cycles=1354; hbm_byte_share=0.983398438.`

## Focused Comparison
- primary_question: `Does explicit HBM controller service change the measured-SRAM Llama7B attention frontier latency or dominant resource?`
- comparison_role: `frontier_closure`
- proposal_outcome: `measured_hbm_service_recorded`
- comparison_summary: `Decoder measured-HBM service evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_measured_hbm_service__l2_decoder_attention_kv_measured_hbm_service_llama7b_v1.json: decision=measured_hbm_service_recorded; latency_us=2138.84136; dominant_tile_resource=tile_attention; effective_hbm_bytes_per_cycle=792.596465; source_effective_hbm_bytes_per_cycle=41341.3632; derived_hbm_efficiency_vs_source=0.019172; controller_service_cycles=1301; tile_attention_cycles=1354; hbm_byte_share=0.983398438.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
