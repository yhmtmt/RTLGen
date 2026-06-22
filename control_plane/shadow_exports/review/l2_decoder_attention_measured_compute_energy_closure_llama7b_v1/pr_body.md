## Summary
- item_id: `l2_decoder_attention_measured_compute_energy_closure_llama7b_v1`
- run_key: `l2_decoder_attention_measured_compute_energy_closure_llama7b_v1_run_14a2a7f71b70d0eb`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_measured_compute_energy_closure_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_measured_compute_energy_closure_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_measured_compute_energy_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `8a1546101a72d36317320f41587d1d400369bc48`
- review_metadata_source_commit: `8a1546101a72d36317320f41587d1d400369bc48`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_measured_compute_energy_closure`
- comparison_role: `frontier_closure`
- expected_direction: `record_measured_compute_energy_closure`
- expected_reason: `Replace the abstract selected MAC/cycle point with measured dense-tile compute capacity before final Llama7B ranking.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_measured_compute_energy_closure__l2_decoder_attention_measured_compute_energy_closure_llama7b_v1.json: decision=measured_compute_constraints_replace_abstract_frontier; recommended_next_step=Use the measured-compute-constrained frontier for the next architecture decision; then either measure a larger integrated compute macro or explore denser/lower-precision compute.`

## Focused Comparison
- primary_question: `Does measured dense-tile compute capacity preserve or replace the current HBM-calibrated Llama7B frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `measured_compute_constraints_replace_abstract_frontier`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_measured_compute_energy_closure__l2_decoder_attention_measured_compute_energy_closure_llama7b_v1.json: decision=measured_compute_constraints_replace_abstract_frontier; recommended_next_step=Use the measured-compute-constrained frontier for the next architecture decision; then either measure a larger integrated compute macro or explore denser/lower-precision compute.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
