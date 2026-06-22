## Summary
- item_id: `l2_decoder_attention_hbm_energy_calibration_llama7b_v1`
- run_key: `l2_decoder_attention_hbm_energy_calibration_llama7b_v1_run_75da55250a5254ab`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_hbm_energy_calibration_llama7b_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_hbm_energy_calibration_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_hbm_energy_calibration_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_hbm_energy_calibration_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `53584274bf7f29e3943ef9c0906a994694cb3908`
- review_metadata_source_commit: `53584274bf7f29e3943ef9c0906a994694cb3908`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_hbm_energy_calibration`
- comparison_role: `frontier_closure`
- expected_direction: `record_source_backed_hbm_energy_calibration`
- expected_reason: `Calibrate the HBM energy component with source-backed HBM stack references before claiming an energy-optimal Llama7B point.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_calibration__l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json: decision=hbm_energy_calibration_preserves_energy_frontier; recommended_next_step=If HBM dominates under source-backed aggregate calibration, replace the aggregate pJ/bit bound with a stack-current/controller-calibrated HBM model before final energy ranking.`

## Focused Comparison
- primary_question: `Does source-backed aggregate HBM pJ/bit calibration preserve or move the Llama7B HBM/DRAM service-energy frontier?`
- comparison_role: `frontier_closure`
- proposal_outcome: `hbm_energy_calibration_preserves_energy_frontier`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_energy_calibration__l2_decoder_attention_hbm_energy_calibration_llama7b_v1.json: decision=hbm_energy_calibration_preserves_energy_frontier; recommended_next_step=If HBM dominates under source-backed aggregate calibration, replace the aggregate pJ/bit bound with a stack-current/controller-calibrated HBM model before final energy ranking.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
