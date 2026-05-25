## Summary
- item_id: `l2_npu_compute_full_path_equivalence_guard_v1`
- run_key: `l2_npu_compute_full_path_equivalence_guard_v1_run_feb36ad11106d282`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `8/8 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_npu_compute_full_path_equivalence_guard_v1/evaluated.json`
- metrics_rows_count: `14`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_npu_compute_full_path_equivalence_guard_v1.json`

## Developer Context
- proposal_id: `prop_l1_npu_corrected_compute_frontier_v1`
- proposal_path: `docs/proposals/prop_l1_npu_corrected_compute_frontier_v1`
- reviewer_first_read: `docs/proposals/prop_l1_npu_corrected_compute_frontier_v1` plus `docs/developer_agent_review.md`
- execution_source_commit: `b2d32a837b3da1bc43a192aecd8f7089cf972c61`
- review_metadata_source_commit: `b2d32a837b3da1bc43a192aecd8f7089cf972c61`

## Evaluation Mode
- evaluation_mode: `correctness_guard`
- abstraction_layer: `npu_compute_full_path_equivalence_guard`
- comparison_role: `precondition`
- expected_direction: `gate`
- expected_reason: `Run PPA sweeps only if corrected datapath guard passes`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs or prior_art.`

## Focused Comparison
- primary_question: `Which corrected FP16 NPU compute module count is the practical PPA anchor once disconnected-output measurements are excluded?`
- comparison_role: `precondition`
- proposal_outcome: `unavailable`
- comparison_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs or prior_art.`
- baseline_ref: `None`
- baseline_item_id: `None`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
