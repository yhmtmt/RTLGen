# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_num_modules_adaptive_v1`
- `candidate_id`: `cand_l2_num_modules_adaptive_v1_r1`

## Pre-Evaluation Context
- The historical imported softmax-tail `num_modules` campaign favored
  `fp16_nm1` over `fp16_nm2`.
- The later accepted mapper-only proposal
  `prop_l2_mapper_memory_aware_split_v1` materially improved the focused `nm2`
  softmax-tail path, which makes the older module-count conclusion stale.

## Consumed Prior Evidence
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/report.md`
- `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/best_point.json`
- `docs/proposals/prop_l2_mapper_memory_aware_split_v1/analysis_report.md`
- `control_plane/shadow_exports/l2_decisions/l2_prop_l2_mapper_memory_aware_split_v1_nm2_focus_r2.json`

## First Evaluation Intent
- rerun the historical `num_modules` campaign under the current code baseline
- compare the fresh `nm1` versus `nm2` result against the old campaign result
- determine whether module-count choice should remain fixed or be treated as
  adaptive for this workload family

## Result
- result: pending
- confidence level: pending
- note: waiting for the first refreshed Layer 2 campaign

## Recommendation
- iterate
- short reason: the proposal is created and the first evaluation request is prepared, but the refreshed architecture evidence has not been produced yet
