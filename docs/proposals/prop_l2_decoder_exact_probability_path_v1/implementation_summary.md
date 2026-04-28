# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_exact_probability_path_v1`
- exact probability-path candidate

## Scope
- switch the active decoder candidate backend to exact softmax and exact
  normalization
- regenerate candidate artifacts for `llm_decoder_eval_tiny_v1`
- preserve the ONNX model, tokenizer, prompt set, top-k setting, and selected
  tensor trace list

## Files Changed
- `runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`
- `runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json`
- `runs/datasets/llm_decoder_eval_tiny_v1/candidate/*.json`
- `runs/models/llm_decoder_tiny_v1/model_contract.json`
- `docs/proposals/prop_l2_decoder_exact_probability_path_v1/*`

## Local Validation
- `python3 npu/eval/gen_llm_decoder_candidate_suite.py`
- `python3 npu/eval/validate_llm_decoder_contract.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest.json --out /tmp/decoder_exact_contract.json`
- `python3 npu/eval/compare_llm_decoder_quality.py --reference-manifest runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json --candidate-manifest runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json --out /tmp/decoder_exact_quality.json`
- `python3 -m unittest tests.test_llm_decoder_quality tests.test_llm_decoder_onnx_runner tests.test_llm_decoder_onnx_candidate_runner tests.test_llm_decoder_compare tests.test_llm_decoder_contract`
- `python3 scripts/validate_runs.py --skip_eval_queue`

Result:
- decoder contract: `ok=true`
- sample count: `5`
- next-token exact-match rate: `1.0`
- top-k containment rate: `1.0`
- selected tensor shape-match rate: `1.0`

## Evaluation Request
- request `l2_decoder_exact_probability_path_v1`
- paired comparison against `l2_decoder_contract_eval_confirm_v1`

## Risks
- this candidate improves quality by using exact probability math; it is a
  quality-preserving reference point, not a final hardware approximation
