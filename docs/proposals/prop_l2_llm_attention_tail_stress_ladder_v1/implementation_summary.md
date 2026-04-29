# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_llm_attention_tail_stress_ladder_v1`
- `title`: `LLM attention-tail stress ladder`

## Scope
- added the `llm_attention_tail_stress_v1` ONNX-lite model generator
- generated three bounded stress attention-tail proxy models
- validated optional deterministic reference and candidate fixture generation
  locally; the large generated JSON fixtures are intentionally not checked in
- added a Layer 2 campaign scaffold using existing `fp16_nm1` and `fp16_nm2`
  architecture points
- documented the stress ladder and proposal-backed evaluation request
- did not change RTL, mapper lowering logic, simulator logic, or scoring code

## Files Changed
- `npu/mapper/examples/gen_llm_attention_tail_stress_suite_lite.py`
- `runs/models/llm_attention_tail_stress_v1/`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/`
- `docs/proposals/prop_l2_llm_attention_tail_stress_ladder_v1/`
- `docs/architecture/llm_attention_benchmark_ladder.md`
- `docs/backlog/items/item_eval_llm_attention_suite_v1.md`
- `runs/models/README.md`
- `npu/mapper/README.md`

## Local Validation
- `python3 -m py_compile npu/mapper/examples/gen_llm_attention_tail_stress_suite_lite.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json --check_paths`
- `python3 npu/eval/gen_llm_reference_suite.py --manifest runs/models/llm_attention_tail_stress_v1/manifest.json`
- `python3 npu/eval/gen_llm_candidate_suite.py --manifest runs/models/llm_attention_tail_stress_v1/manifest.json`
- `python3 npu/eval/compare_llm_reference.py --reference-json runs/models/llm_attention_tail_stress_v1/reference/tail_attn6_s256_h64.json --candidate-json runs/models/llm_attention_tail_stress_v1/candidate/tail_attn6_s256_h64.json`
- `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json --repeat 1 --max_models 1 --max_arch 1 --modes flat_nomacro --jobs 1 --batch_id local_stress_smoke`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Evaluation Request
- item: `l2_llm_attention_tail_stress_ladder_v1`
- task type: `l2_campaign`
- evaluation mode: `broad_ranking`
- platform: `nangate45`

## Risks
- This is still an attention-tail proxy, not a decoder-quality benchmark.
- If pressure remains low at this size, the next step should be a practical
  decoder-style workload rather than another softmax micro-architecture change.
