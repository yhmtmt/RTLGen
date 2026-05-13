## Summary
- item_id: `l2_decoder_attention_kv_memory_measured_tile_v1`
- run_key: `l2_decoder_attention_kv_memory_measured_tile_v1_run_e6b4091c9ebc7af0`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_memory_measured_tile_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_measured_tile_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_memory_measured_tile_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_memory_measured_tile_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_memory_measured_tile_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `b748dcf4eb5ce17a104ca4a26328f032f5cb9040`
- review_metadata_source_commit: `b748dcf4eb5ce17a104ca4a26328f032f5cb9040`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_memory`
- comparison_role: `calibrated_refresh`
- expected_direction: `iterate`
- expected_reason: `Confirm whether measured tile PPA changes the attention/KV bottleneck map before producer/memory/NoC coupled RTL work is queued.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_measured_tile_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `Do the accepted Layer 1 attention/KV tile measurements materially change the Layer 2 attention/KV memory bottleneck map and next-job priority?`
- comparison_role: `calibrated_refresh`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_attention_kv_memory_measured_tile_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
