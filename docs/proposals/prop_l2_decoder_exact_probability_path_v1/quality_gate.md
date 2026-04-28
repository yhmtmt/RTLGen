# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_exact_probability_path_v1`
- `title`: `LLM decoder exact probability-path candidate`

## Why This Gate Is Required
- this proposal changes the active decoder candidate semantics and therefore
  must prove token-quality behavior rather than only structural validity

## Reference
- baseline_ref: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_compare__l2_decoder_contract_eval_confirm_v1.json`
- reference_ref: `runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json`

## Checks
- metric: `next_token_id_match_rate`
  - threshold: `> 0.8`
- metric: `topk_contains_reference_id_rate`
  - threshold: `> 0.8`
- metric: `selected_tensor_trace.shape_match_rate`
  - threshold: `1.0`
- metric: `missing_model_check.ok`
  - threshold: `true`

## Local Commands
- command: `python3 npu/eval/gen_llm_decoder_candidate_suite.py`
- command: `python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`
- command: `python3 npu/eval/compare_llm_decoder_quality.py --reference-manifest runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json --candidate-manifest runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json`

## Result
- status: local_pass
- note: local regenerated candidate artifacts reach `1.0` next-token exact-match and top-k containment, with selected tensor shape-match rate still `1.0`; evaluator evidence is still required before promotion.
