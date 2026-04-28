## Summary
- item_id: `l2_decoder_exact_probability_path_v1`
- run_key: `l2_decoder_exact_probability_path_v1_run_930a1658a4e342e8`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_exact_probability_path_v1/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_exact_probability_path_v1.json`

## Developer Context
- proposal_id: `prop_l2_decoder_exact_probability_path_v1`
- proposal_path: `docs/proposals/prop_l2_decoder_exact_probability_path_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l2_decoder_exact_probability_path_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `251d3fddd95a52d4555d670cf3b95bec26a4d0b7`
- review_metadata_source_commit: `251d3fddd95a52d4555d670cf3b95bec26a4d0b7`

## Evaluation Mode
- evaluation_mode: `paired_comparison`
- abstraction_layer: `decoder_probability_path`
- comparison_role: `candidate`
- expected_direction: `better_than_historical`
- expected_reason: `Exact probability path should improve over the prior 0.8 exact/top-k decoder rates while preserving the contract.`
- expectation_status: `unexpected`
- evaluation_summary: `Focused comparison matched the baseline with no measurable latency or energy delta.`

## Focused Comparison
- primary_question: `Does the exact probability-path candidate improve the llm_decoder_eval_tiny_v1 token-quality gate relative to the prior q4 PWL softmax plus quantized reciprocal candidate?`
- comparison_role: `candidate`
- proposal_outcome: `no_measurable_change`
- comparison_summary: `Focused comparison matched the baseline with no measurable latency or energy delta.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_contract_eval_confirm_v1`
- baseline_item_id: `l2_decoder_contract_eval_confirm_v1`
- latency_delta fp16_nm1/flat_nomacro/mlp1: `0.004282` -> `0.004282` ms
- energy_delta fp16_nm1/flat_nomacro/mlp1: `8.26948404e-07` -> `8.26948404e-07` mJ
- latency_delta fp16_nm1/flat_nomacro/mlp2: `0.05353399999999999` -> `0.05353399999999999` ms
- energy_delta fp16_nm1/flat_nomacro/mlp2: `1.0338593148e-05` -> `1.0338593148e-05` mJ

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
