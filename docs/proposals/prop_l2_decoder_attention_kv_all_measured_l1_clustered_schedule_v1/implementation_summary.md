# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1`
- `title`: `All-measured Llama7B attention L2 clustered schedule`

## Scope
- generated an L2 campaign retry for the all-measured L1 attention cost stack
- reused merged measured compute-array PPA for `fp16_nm1` and `fp16_nm2`
- consumed full-value tile, exact softmax generator, and local NoC/SRAM profile
  references
- did not introduce new RTL or mapper changes in this result PR

## Files Changed
- `docs/proposals/prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1/`
- `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1__l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4/`
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4.json`
- `control_plane/shadow_exports/review/l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4/`

## Local Validation
- `python3 scripts/validate_runs.py --skip_eval_queue`: executed by CI and
  passed on PR #746.

## Evaluation Request
- item: `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`
- mode: `broad_ranking`
- expected result: quantify whether the all-measured local stack shifts the
  previous full-value clustered frontier.

## Risks
- SRAM capacity/service and global NoC arbitration remain analytic service
  terms.
- The ranked compute anchors are limited to `fp16_nm1` and `fp16_nm2`.
- The submitted campaign artifacts are a review record; follow-on frontier
  jobs still need physically constrained memory and global interconnect blocks.

