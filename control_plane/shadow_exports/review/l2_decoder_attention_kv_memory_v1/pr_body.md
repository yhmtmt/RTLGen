## Summary
- item_id: `l2_decoder_attention_kv_memory_v1`
- run_key: `l2_decoder_attention_kv_memory_v1_run_2f4bfb7205516a28`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_kv_memory_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_memory_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_attention_kv_memory_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_attention_kv_memory_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_attention_kv_memory_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `ad209a1f7502b1b4559fe3214c89613e6898c1ca`
- review_metadata_source_commit: `ad209a1f7502b1b4559fe3214c89613e6898c1ca`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_attention_kv_memory`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `The expected output is an attention/KV bottleneck map used to choose whether the next architecture job should measure KV memory hierarchy, NoC coupling, or attention compute datapath.`
- expectation_status: `unspecified`
- evaluation_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`

## Focused Comparison
- primary_question: `Across GPT-2-like and larger proxy shapes, which attention substage dominates when sequence length, compute throughput, KV memory tier, NoC hops, KV precision, and MHA/GQA/MQA sharing are varied?`
- comparison_role: `ranking`
- proposal_outcome: `ranking_recorded`
- comparison_summary: `Ranking/frontier evidence was recorded for this proposal; focused baseline comparison is not required for this evaluation mode.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
