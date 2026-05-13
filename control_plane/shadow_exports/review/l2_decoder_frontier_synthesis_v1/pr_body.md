## Summary
- item_id: `l2_decoder_frontier_synthesis_v1`
- run_key: `l2_decoder_frontier_synthesis_v1_run_e59761847807d227`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `9/9 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_frontier_synthesis_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_frontier_synthesis_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_frontier_synthesis_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_frontier_synthesis_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_frontier_synthesis_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `babb33627fd6a8c6305f28fe82e3b70c319f6f3a`
- review_metadata_source_commit: `babb33627fd6a8c6305f28fe82e3b70c319f6f3a`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_frontier_synthesis`
- comparison_role: `frontier_synthesis`
- expected_direction: `iterate`
- expected_reason: `The output should identify whether the next measured RTL job should focus on producer/ranker, attention/KV memory hierarchy, or another whole-decoder bottleneck.`
- expectation_status: `unspecified`
- evaluation_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_frontier_synthesis_v1.json: decision=decoder_evidence_recorded.`

## Focused Comparison
- primary_question: `When measured attention/KV tile PPA, producer/ranker NoC coupling, and whole-decoder stage breakdown are compared together, which component dominates the next RTL frontier?`
- comparison_role: `frontier_synthesis`
- proposal_outcome: `decoder_evidence_recorded`
- comparison_summary: `Decoder quality evidence recorded from runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_memory__l2_decoder_frontier_synthesis_v1.json: decision=decoder_evidence_recorded.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
