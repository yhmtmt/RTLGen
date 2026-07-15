## Summary
- item_id: `l2_decoder_attention_operational_component_frontier_llama7b_v1`
- run_key: `l2_decoder_attention_operational_component_frontier_llama7b_v1_run_3da24c3e1b774672`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_operational_component_frontier_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_operational_component_frontier_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_operational_cluster_physical_closure_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `12e07e61c696e5724c038ba5343dbe73f73770da`
- review_metadata_source_commit: `12e07e61c696e5724c038ba5343dbe73f73770da`

## Evaluation Mode
- evaluation_mode: `frontier_recost`
- abstraction_layer: `decoder_attention_operational_component_frontier`
- comparison_role: `operational_component_frontier_recost`
- expected_direction: `reprice_frontier_with_operational_components`
- expected_reason: `Use measured component area/timing while retaining activity-backed token energy until SAIF/VCD calibration.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder operational-component frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_operational_component_frontier__l2_decoder_attention_operational_component_frontier_llama7b_v1.json: decision=operational_component_area_timing_recosted_energy_retained; recommended_candidate=score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components; recommended_latency_us=1595.42090302109; recommended_token_throughput_per_s=626.793843622331; recommended_energy_mj_per_token=137.330868813197; recommended_embodied_area_mm2=325.5239481009; energy_promotion_blocked=True; next_step=measure activity-backed operational tile power and physically compose one local cluster.`

## Focused Comparison
- primary_question: `How far do operational accumulator state, banked SRAM wiring, divider sharing, and local cluster routing move the measured Llama7B throughput, energy, and area frontier?`
- comparison_role: `operational_component_frontier_recost`
- proposal_outcome: `operational_component_area_timing_recosted_energy_retained`
- comparison_summary: `Decoder operational-component frontier recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_operational_component_frontier__l2_decoder_attention_operational_component_frontier_llama7b_v1.json: decision=operational_component_area_timing_recosted_energy_retained; recommended_candidate=score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components; recommended_latency_us=1595.42090302109; recommended_token_throughput_per_s=626.793843622331; recommended_energy_mj_per_token=137.330868813197; recommended_embodied_area_mm2=325.5239481009; energy_promotion_blocked=True; next_step=measure activity-backed operational tile power and physically compose one local cluster.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
