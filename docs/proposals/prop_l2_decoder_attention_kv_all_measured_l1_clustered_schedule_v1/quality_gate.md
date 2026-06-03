# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1`
- `title`: `All-measured Llama7B attention L2 clustered schedule`

## Why This Gate Is Required
The result changes the L2 attention ranking evidence by adding exact softmax
weight generator and local NoC costs to the measured local stack. The output is
used to guide later Llama7B frontier jobs, so the evidence must distinguish
measured local datapath blocks from residual analytic memory/interconnect terms.

## Reference
- baseline_ref: `item:l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- reference_ref: `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json`

## Checks
- command_success:
  - threshold: all requested commands must succeed
- artifact_sync:
  - threshold: proposal package, decision proposal, and campaign outputs must be
    materialized in the review PR
- residual_abstraction_visibility:
  - threshold: SRAM and global NoC assumptions must be recorded in proposal and
    decision artifacts

## Local Commands
- command: `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed
- note: PR #746 CI passed and the work item advanced from `artifact_sync` to
  `awaiting_review`; the result remains an iteration baseline, not a final
  promotion.

