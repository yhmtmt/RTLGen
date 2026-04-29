# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_llm_attention_tail_stress_ladder_v1`
- `title`: `LLM attention-tail stress ladder`

## Why This Gate Is Required
The proposal adds benchmark inputs and a campaign scaffold used for architecture
planning. The quality gate checks that the new generated model set is
repo-portable, path-valid, and connected to a proposal-backed evaluation item.

## Reference
- proposal: `docs/proposals/prop_l2_llm_attention_tail_stress_ladder_v1/proposal.json`
- campaign: `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json`
- model set: `runs/models/llm_attention_tail_stress_v1/manifest.json`

## Checks
- generator syntax:
  - threshold: `python3 -m py_compile` passes
- campaign path validation:
  - threshold: `npu/eval/validate.py --check_paths` passes
- optional numerical fixture generation:
  - threshold: reference/candidate generation and one largest-model comparison
    pass locally; generated JSON fixtures are not checked in
- mapper/perf smoke:
  - threshold: one local `run_campaign.py` sample lowers the first stress model
    and emits a perf trace
- run index validation:
  - threshold: `scripts/validate_runs.py --skip_eval_queue` passes
- evaluator packaging:
  - threshold: generated review package resolves
    `docs/proposals/prop_l2_llm_attention_tail_stress_ladder_v1/proposal.json`

## Local Commands
- `python3 -m py_compile npu/mapper/examples/gen_llm_attention_tail_stress_suite_lite.py`
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json --check_paths`
- `python3 npu/eval/gen_llm_reference_suite.py --manifest runs/models/llm_attention_tail_stress_v1/manifest.json`
- `python3 npu/eval/gen_llm_candidate_suite.py --manifest runs/models/llm_attention_tail_stress_v1/manifest.json`
- `python3 npu/eval/compare_llm_reference.py --reference-json runs/models/llm_attention_tail_stress_v1/reference/tail_attn6_s256_h64.json --candidate-json runs/models/llm_attention_tail_stress_v1/candidate/tail_attn6_s256_h64.json`
- `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json --repeat 1 --max_models 1 --max_arch 1 --modes flat_nomacro --jobs 1 --batch_id local_stress_smoke`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: local-pass
- note: local syntax, path, reference-comparison, run-index, and one-sample
  mapper/perf smoke checks passed; remote campaign execution remains pending.
