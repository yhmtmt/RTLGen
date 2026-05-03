## Summary
- item_id: `l2_decoder_pwl_bitwidth_boundary_v1`
- run_key: `l2_decoder_pwl_bitwidth_boundary_v1_run_5f8b6f46e6c2fe4b`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `11/11 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_pwl_bitwidth_boundary_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_pwl_bitwidth_boundary_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_pwl_bitwidth_boundary_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_pwl_bitwidth_boundary_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_pwl_bitwidth_boundary_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `735732d900d085082382db7777763b1afd1aad56`
- review_metadata_source_commit: `735732d900d085082382db7777763b1afd1aad56`

## Evaluation Mode
- evaluation_mode: `frontier_detail`
- abstraction_layer: `decoder_pwl_bitwidth_boundary`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Determine whether q11 is exact-safe before spending another Layer 1 PPA run, or keep q12 as the integer exact-safe floor.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Across the expanded v2 prompt distribution, is q11 PWL exact-normalization enough to preserve exact next-token and top-k behavior, or does q12 remain the lowest exact-safe integer PWL bit width?`
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
