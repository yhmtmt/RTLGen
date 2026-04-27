## Summary
- item_id: `l2_llm_attention_tail_v1_nangate45_r1`
- run_key: `l2_llm_attention_tail_v1_nangate45_r1_run_be2fd33c8cfd917e`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `5/5 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_llm_attention_tail_v1_nangate45_r1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_llm_attention_tail_v1_nangate45_r1.json`

## Developer Context
- proposal_id: `prop_l2_llm_attention_tail_v1`
- proposal_path: `docs/proposals/prop_l2_llm_attention_tail_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_llm_attention_tail_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `e0010e569dcbf4f4da47802bfed745545e49e563`
- review_metadata_source_commit: `813d7a7166e961da4105e4c326b6ab14120356db`

## Evaluation Mode
- evaluation_mode: `broad_ranking`
- abstraction_layer: `layer2`
- comparison_role: `ranking`
- expected_direction: `collect_evidence`
- expected_reason: `Measure per-token latency, throughput, softmax occupancy, stall buckets, and overlap/backpressure before launching softmax architecture proposals.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Which current architecture point best supports LLM attention-tail scheduling evidence?`
- comparison_role: `ranking`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
