# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_llm_attention_tail_v1`
- `title`: `LLM attention tail measurement gate`

## Scope
- added proposal-backed review metadata for the LLM attention-tail Layer 2 run
- generated the concrete campaign request for
  `l2_llm_attention_tail_v1_nangate45_r1`
- collected campaign outputs and focused mapper/perf artifacts for the
  top-ranked point
- did not change RTL, mapper logic, simulator logic, or campaign scoring code

## Files Changed
- `docs/proposals/prop_l2_llm_attention_tail_v1/`
- `control_plane/shadow_exports/review/l2_llm_attention_tail_v1_nangate45_r1/`
- `control_plane/shadow_exports/l2_decisions/l2_llm_attention_tail_v1_nangate45_r1.json`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/`

## Local Validation
- `python3 npu/eval/validate.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json --check_paths`: passed during evaluation
- `python3 npu/eval/run_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json --run_physical --jobs 2 --batch_id l2_llm_attention_tail_v1_nangate45_r1_r1`: passed during evaluation
- `python3 npu/eval/report_campaign.py --campaign runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign__l2_llm_attention_tail_v1_nangate45_r1.json`: passed during evaluation
- `python3 scripts/validate_runs.py --skip_eval_queue`: passed

## Evaluation Request
- item: `l2_llm_attention_tail_v1_nangate45_r1`
- run: `l2_llm_attention_tail_v1_nangate45_r1_run_be2fd33c8cfd917e`
- task type: `l2_campaign`
- evaluation mode: `broad_ranking`
- platform: `nangate45`

## Risks
- This is a measurement gate, so it does not isolate a paired baseline delta.
- Current softmax scheduler metrics show no backpressure in this workload set;
  the next proposal may need a more stressful model shape or mapper schedule to
  expose softmax-specific headroom.
