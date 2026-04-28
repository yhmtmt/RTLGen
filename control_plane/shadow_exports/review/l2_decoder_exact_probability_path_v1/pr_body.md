## Summary
- item_id: `l2_decoder_exact_probability_path_v1`
- run_key: `l2_decoder_exact_probability_path_v1_run_930a1658a4e342e8`
- layer: `layer2`
- task_type: `l2_campaign`
- status: `ok`
- summary: `9/9 commands succeeded; Decoder quality improved from 0.8 to 1.0 exact/top-k on 5 samples; campaign physical metrics matched the paired baseline.`
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
- expectation_status: `met`
- evaluation_summary: `Decoder quality improved from 0.8 to 1.0 exact/top-k on 5 samples; campaign physical metrics matched the paired baseline.`

## Decoder Evidence
- baseline_semantics: `onnx_logits_fp_softmax_approx_pwl_in_q4_w_q4_norm_recip_q10_prob_fp`
- candidate_semantics: `onnx_logits_fp_softmax_exact_norm_exact_prob_fp`
- next_token_exact_rate: `0.8` -> `1.0`
- topk_contains_reference_rate: `0.8` -> `1.0`
- selected_tensor_shape_match: `20/20`
- missing_model_error: `NoSuchFile` check `true`
- contract_validation: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_contract_validation__l2_decoder_exact_probability_path_v1.json`
- quality_comparison: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_compare__l2_decoder_exact_probability_path_v1.json`
- missing_model_check: `runs/datasets/llm_decoder_eval_tiny_v1/missing_model_check__l2_decoder_exact_probability_path_v1.json`

## Focused Comparison
- primary_question: `Does the exact probability-path candidate improve the llm_decoder_eval_tiny_v1 token-quality gate relative to the prior q4 PWL softmax plus quantized reciprocal candidate?`
- comparison_role: `candidate`
- proposal_outcome: `quality_improved`
- comparison_summary: `Decoder quality improved from 0.8 to 1.0 exact/top-k on 5 samples; campaign physical metrics matched the paired baseline.`
- baseline_ref: `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_contract_eval_confirm_v1`
- baseline_item_id: `l2_decoder_contract_eval_confirm_v1`
- campaign_physical_result: `no measurable latency or energy delta on the smoke campaign`

## Checklist
- [x] Commit lightweight campaign artifacts only
- [x] Include metrics row references in result.metrics_rows
- [x] Keep committed result_path fields repo-portable
- [x] Run python3 scripts/validate_runs.py --skip_eval_queue before pushing
