# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_llm_attention_tail_v1`
- `title`: `LLM attention tail measurement gate`

## Why This Gate Is Required
The proposal records measurement evidence rather than changing functional RTL.
The quality gate checks that the campaign is complete, repo-portable, and
validated before it is used as architecture-planning evidence.

## Reference
- proposal: `docs/proposals/prop_l2_llm_attention_tail_v1/proposal.json`
- campaign: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json`
- report: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/report.md`

## Checks
- campaign path validation:
  - threshold: `npu/eval/validate.py --check_paths` passes
- campaign completion:
  - threshold: `60/60` result rows are `ok`
- review package portability:
  - threshold: committed `result_path`, source refs, and proposal links are
    repo-relative
- run index validation:
  - threshold: `scripts/validate_runs.py --skip_eval_queue` passes

## Local Commands
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json --check_paths`
- `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json --run_physical --jobs 2 --batch_id l2_llm_attention_tail_v1_nangate45_r1_r1`
- `python3 npu/eval/report_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json`
- `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed
- note: The evidence PR records `5/5` successful commands, `60` ok campaign
  rows, `24` summary rows, and a passing run validation.
