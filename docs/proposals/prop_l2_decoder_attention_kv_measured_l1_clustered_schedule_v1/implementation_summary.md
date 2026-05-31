# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`

## Scope
- Added measured L1 cost-profile support to the clustered attention estimator.
- Charged measured per-cluster local datapath, FIFO, and router area against
  the logic budget before compute-replica allocation.
- Added measured L1 power and max local clock fields to the result rows.
- Registered the `decoder_attention_kv_measured_l1_clustered_schedule` L2
  control-plane abstraction.

## Files Changed
- `npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py`
- `control_plane/control_plane/services/l2_task_generator.py`
- `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_v1.json`
- `tests/test_llm_decoder_attention_kv_clustered_schedule.py`

## Local Validation
- `/workspaces/RTLGen/control_plane/.venv/bin/python -m pytest tests/test_llm_decoder_attention_kv_clustered_schedule.py`
- `python3 -m py_compile npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py control_plane/control_plane/services/l2_task_generator.py`
- `python3 scripts/validate_runs.py --skip_eval_queue`
- Direct measured-L1 estimator smoke run.

## Evaluation Request
- item: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- run: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1_run_13be6b847e98c296`
- source commit: `0a1e86e0bce5672d52eb4b831971c0858bc84fab`

## Risks
- The measured L1 profile is still a proxy for the local tile/reducer path,
  not full value-path closure.
- NoC/SRAM behavior remains analytic bandwidth/hop modeling.
- The broad frontier still depends on the measured compute candidates and the
  assumed die budget allocation.
