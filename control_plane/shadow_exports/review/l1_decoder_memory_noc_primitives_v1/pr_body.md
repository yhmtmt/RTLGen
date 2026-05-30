## Summary
- item_id: `l1_decoder_memory_noc_primitives_v1`
- run_key: `l1_decoder_memory_noc_primitives_v1_run_2bfbafba92a23051`
- layer: `layer1`
- task_type: `l1_sweep`
- status: `ok`
- summary: `4/4 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l1_decoder_memory_noc_primitives_v1/evaluated.json`
- metrics_rows_count: `12`
- review_artifact: `promotion_proposal` at `control_plane/shadow_exports/l1_promotions/l1_decoder_memory_noc_primitives_v1.json`

## Developer Context
- proposal_id: `prop_l1_decoder_memory_noc_primitives_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_memory_noc_primitives_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_memory_noc_primitives_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `3092a61412e191e4471b35d38f57c19ffd4e5842`
- review_metadata_source_commit: `05f507cbb795e999133152da7eb87f090b95dbed`

## Evaluation Mode
- evaluation_mode: `ppa`
- abstraction_layer: `architecture_block`
- evaluation_summary: `Physical metrics recorded from an accepted status=ok Layer 1 row.`

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l1_decoder_memory_noc_primitives_v1 is not eligible for submission: developer_loop proposal linkage does not resolve to a proposal`

## Checklist
- [ ] Commit only lightweight metrics; shared runs/index.csv is exported centrally after merge
- [ ] Include metrics row references for each completed design
- [ ] Run python3 scripts/build_runs_index.py and python3 scripts/validate_runs.py --skip_eval_queue before pushing
