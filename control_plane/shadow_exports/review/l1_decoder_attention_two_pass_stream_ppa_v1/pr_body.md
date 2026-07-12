## Summary
- item_id: `l1_decoder_attention_two_pass_stream_ppa_v1`
- run_key: `l1_decoder_attention_two_pass_stream_ppa_v1_run_d88cdb5818618a63`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `18/18 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_attention_two_pass_stream_ppa_v1/evaluated.json`
- metrics_rows_count: `8`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_two_pass_stream_ppa_v1.json`

## Developer Context
- proposal_id: `prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1`
- proposal_path: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_decoder_attention_hierarchical_softmax_frontier_llama7b_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `636d3d67ff149b5fa9066750d26240d7723c11b0`
- review_metadata_source_commit: `84c0c4434d89f2e45680abbd948b1ae4ad75aba9`

## Evaluation Mode
- evaluation_mode: `frontier_followup`
- abstraction_layer: `decoder_attention_two_pass_stream`
- evaluation_summary: `No timing-feasible Layer 1 rows were produced; completed flows that miss their declared clock period are retained as explicit timing-boundary evidence.`

## Focused Comparison
- proposal_outcome: `boundary_no_feasible_points`
- comparison_summary: `All completed physical rows miss their declared clock period; retain them as timing-boundary evidence and do not promote a feasible design point.`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `Command '['git', 'push', '--force-with-lease', '-u', 'origin', 'eval/l1_decoder_attention_two_pass_stream_ppa_v1/s20260710t231825z']' returned non-zero exit status 1.`
- final_submission_pr: `https://github.com/yhmtmt/RTLGen/pull/1256`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
