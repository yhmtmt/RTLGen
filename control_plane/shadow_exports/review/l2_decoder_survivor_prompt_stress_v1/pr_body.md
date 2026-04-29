## Summary
- item_id: `l2_decoder_survivor_prompt_stress_v1`
- run_key: `l2_decoder_survivor_prompt_stress_v1_run_13396e7948b2b9ae`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `10/10 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_survivor_prompt_stress_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_survivor_prompt_stress_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_survivor_prompt_stress_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_survivor_prompt_stress_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_survivor_prompt_stress_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `3cf7f0e69ef21d95b1a3dcbfa88b13d0c5d563a7`
- review_metadata_source_commit: `3cf7f0e69ef21d95b1a3dcbfa88b13d0c5d563a7`

## Evaluation Mode
- evaluation_mode: `focused_stress`
- abstraction_layer: `decoder_survivor_prompt_stress`
- comparison_role: `ranking`
- expected_direction: `iterate`
- expected_reason: `Confirm whether survivor paths remain stable across a larger prompt set before hardware-cost-oriented narrowing.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison baseline could not be resolved from proposal baseline_refs.`

## Focused Comparison
- primary_question: `Across a larger prompt-stress sample set, do the surviving integer-logit, fp probability, and approximate PWL softmax paths preserve next-token and top-k rank?`
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
