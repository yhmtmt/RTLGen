# Implementation Summary

## Current State
- No new RTL, mapper, or benchmark code change is proposed in this first stage.
- The proposal reuses the existing imported softmax-tail `num_modules` campaign
  to refresh architecture evidence under the current accepted mapper baseline.

## First Evaluation Plan
- rerun:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/campaign.json`
- compare:
  - fresh `fp16_nm1` versus `fp16_nm2` results under current code
  - against the historical campaign report and best-point artifacts

## Expected Deliverable
- one refreshed Layer 2 campaign result that answers whether the old `nm1`
  advantage still holds after the mapper baseline changed
- if ambiguous, a follow-on proposal can widen benchmark coverage or objective
  weighting; that is explicitly out of scope for the first pass
