## Summary
- item_id: `l2_decoder_attention_kv_capacity_noc_baseline_v1`
- run_key: `l2_decoder_attention_kv_capacity_noc_baseline_v1_run_628ac206fbfe767f`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_capacity_noc_baseline_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_capacity_noc_baseline_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_capacity_noc_baseline_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_capacity_noc_baseline_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_capacity_noc_baseline_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `643bc642be773f5cd543761016ec5a940e40d0b7`
- review_metadata_source_commit: `643bc642be773f5cd543761016ec5a940e40d0b7`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_capacity_noc`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `Use capacity-feasible best points to choose the next integrated attention/KV SRAM and NoC scheduling measurement.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_capacity_noc__l2_decoder_attention_kv_capacity_noc_baseline_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `How does the best feasible attention/KV memory placement move as die area, SRAM fraction, usable SRAM, density, banking, NoC bandwidth, and hop count vary?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_capacity_noc__l2_decoder_attention_kv_capacity_noc_baseline_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
