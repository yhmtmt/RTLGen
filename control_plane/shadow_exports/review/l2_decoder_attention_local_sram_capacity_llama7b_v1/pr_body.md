## Summary
- item_id: `l2_decoder_attention_local_sram_capacity_llama7b_v1`
- run_key: `l2_decoder_attention_local_sram_capacity_llama7b_v1_run_2d4c172783f15d4e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_local_sram_capacity_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_local_sram_capacity_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_local_sram_capacity_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_local_sram_capacity_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_local_sram_capacity_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e51e229abbb25947df144d019d8e545e6d85bf05`
- review_metadata_source_commit: `e51e229abbb25947df144d019d8e545e6d85bf05`

## Evaluation Mode
- evaluation_mode: `profile_measurement`
- abstraction_layer: `decoder_attention_local_sram_capacity`
- comparison_role: `frontier_closure`
- expected_direction: `measure_selected_local_sram_capacity_macro_profile`
- expected_reason: `The result should report per-cluster and all-cluster SRAM area/access/energy and budget fit.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder local SRAM capacity evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_local_sram_capacity__l2_decoder_attention_local_sram_capacity_llama7b_v1.json: decision=local_sram_capacity_budget_failed; fits_sram_budget=False; total_area_um2=1306824061.5888963; sram_budget_area_um2=280000000.0; area_fraction_of_sram_budget=4.667229.`

## Focused Evidence
- primary_question: `How much area and access time does the selected local SRAM capacity pool require when represented as concrete SRAM macro chunks?`
- comparison_role: `frontier_closure`
- proposal_outcome: `local_sram_capacity_budget_failed`
- comparison_summary: `Decoder local SRAM capacity evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_local_sram_capacity__l2_decoder_attention_local_sram_capacity_llama7b_v1.json: decision=local_sram_capacity_budget_failed; fits_sram_budget=False; total_area_um2=1306824061.5888963; sram_budget_area_um2=280000000.0; area_fraction_of_sram_budget=4.667229.`
- decoder_evidence_ref: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_local_sram_capacity__l2_decoder_attention_local_sram_capacity_llama7b_v1.json`
- fits_sram_budget: `False`
- total_area_um2: `1306824061.5888963`
- sram_budget_area_um2: `280000000.0`
- area_fraction_of_sram_budget: `4.667229`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
