## Summary
- item_id: `l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3`
- run_key: `l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3_run_933f01e40b51b510`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `6/6 commands succeeded`
- queue_snapshot: `control_plane/shadow_exports/review/l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3/evaluated.json`
- metrics_rows_count: `24`
- review_artifact: `decision_proposal` at `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3.json`

## Developer Context
- proposal_id: `prop_l1_decoder_attention_softmax_recip_lut_frontier_v1`
- proposal_path: `docs/proposals/prop_l1_decoder_attention_softmax_recip_lut_frontier_v1/proposal.json`
- reviewer_first_read: `docs/proposals/prop_l1_decoder_attention_softmax_recip_lut_frontier_v1/proposal.json` plus `docs/developer_agent_review.md`
- execution_source_commit: `a91a3faacea5146ec5b677118537848618f03edd`
- review_metadata_source_commit: `2b5cee9a1984a7b6ec55398cfdc9f2f31fb8191f`

## Evaluation Mode
- evaluation_mode: `quality_equivalence_gate`
- abstraction_layer: `decoder_attention_softmax_recip_lut_quality`
- comparison_role: `softmax_reciprocal_lut_quality_gate`
- expected_direction: `quality_gate_recip_lut`
- expected_reason: `Separate softmax-normalization error from the already-known mixed-precision Q8/K8/V6 quantization error.`
- expectation_status: `unspecified`
- evaluation_summary: `Focused comparison matched the baseline with no measurable latency or energy delta.`

## Focused Comparison
- primary_question: `Can a bounded reciprocal-LUT softmax normalization keep exact-like quality while preserving most of the divider-free PPA gain?`
- comparison_role: `softmax_reciprocal_lut_quality_gate`
- proposal_outcome: `no_measurable_change`
- comparison_summary: `Focused comparison matched the baseline with no measurable latency or energy delta.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_mixed_precision_quality_llama7b_v1__l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1`
- baseline_item_id: `l2_decoder_attention_softmax_pow2sum_quality_llama7b_v1`
- latency_delta fp16_nm1/flat_nomacro/mlp1: `0.004282` -> `0.004282` ms
- energy_delta fp16_nm1/flat_nomacro/mlp1: `8.26948404e-07` -> `8.26948404e-07` mJ
- latency_delta fp16_nm1/flat_nomacro/mlp2: `0.05353399999999999` -> `0.05353399999999999` ms
- energy_delta fp16_nm1/flat_nomacro/mlp2: `1.0338593148e-05` -> `1.0338593148e-05` mJ

## Submission Recovery
- submission_failure_count: `1`
- retry_request_count: `0`
- last_submission_failure: `work item l2_decoder_attention_softmax_recip_lut_quality_llama7b_v1_r3 is not ready for artifact sync from state=blocked`

## Checklist
- [ ] Commit lightweight campaign artifacts only
- [ ] Include metrics row references in result.metrics_rows
- [ ] Keep committed result_path fields repo-portable
- [ ] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
