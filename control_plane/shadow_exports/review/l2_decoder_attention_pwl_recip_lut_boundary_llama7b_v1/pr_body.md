## Summary
- item_id: `l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1`
- run_key: `l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1_run_1702d173031660ca`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `2/2 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1/evaluated.json`
- metrics_rows_count: `0`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `a4cdd1137b7439085eda2bbc742d7eb2cdec1058`
- review_metadata_source_commit: `a4cdd1137b7439085eda2bbc742d7eb2cdec1058`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_pwl_recip_lut_boundary`
- comparison_role: `pwl_recip_lut_synthesis_boundary`
- expected_direction: `bound_direct_lut_before_q20_q24_ppa`
- expected_reason: `q20/q24 PWL candidates passed bounded generation quality, but direct reciprocal-LUT case count grows with weight precision; avoid dispatching q24 OpenROAD PPA that mostly measures LUT explosion.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder attention PWL reciprocal-LUT boundary evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_pwl_recip_lut_boundary__l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1.json: decision=compact_reciprocal_required_for_widest_points; candidate_count=3; reasonable_direct_lut_candidate_count=1; boundary_probe_candidate_count=1; blocked_direct_lut_candidate_count=1; qkv8_q12_pwl_recip_q12_bucket8_cases=128; qkv8_q12_pwl_recip_q12_bucket8_verdict=direct_lut_ppa_reasonable; qkv8_q20_pwl_recip_q20_bucket8_cases=32768; qkv8_q20_pwl_recip_q20_bucket8_verdict=boundary_probe_only; qkv8_q24_pwl_recip_q24_bucket8_cases=524288; qkv8_q24_pwl_recip_q24_bucket8_verdict=requires_compact_reciprocal_before_ppa.`

## Focused Comparison
- comparison_role: `pwl_recip_lut_synthesis_boundary`
- proposal_outcome: `compact_reciprocal_required_for_widest_points`
- comparison_summary: `Decoder attention PWL reciprocal-LUT boundary evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_pwl_recip_lut_boundary__l2_decoder_attention_pwl_recip_lut_boundary_llama7b_v1.json: decision=compact_reciprocal_required_for_widest_points; candidate_count=3; reasonable_direct_lut_candidate_count=1; boundary_probe_candidate_count=1; blocked_direct_lut_candidate_count=1; qkv8_q12_pwl_recip_q12_bucket8_cases=128; qkv8_q12_pwl_recip_q12_bucket8_verdict=direct_lut_ppa_reasonable; qkv8_q20_pwl_recip_q20_bucket8_cases=32768; qkv8_q20_pwl_recip_q20_bucket8_verdict=boundary_probe_only; qkv8_q24_pwl_recip_q24_bucket8_cases=524288; qkv8_q24_pwl_recip_q24_bucket8_verdict=requires_compact_reciprocal_before_ppa.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
