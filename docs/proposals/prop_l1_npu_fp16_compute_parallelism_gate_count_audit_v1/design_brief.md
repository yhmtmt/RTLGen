# Design Brief

## Proposal
- `proposal_id`: `prop_l1_npu_fp16_compute_parallelism_gate_count_audit_v1`
- `title`: `NPU FP16 compute parallelism gate-count audit`

## Problem
- The current FP16 compute parallelism data shows `nm4` as unusually attractive
  in timing and power.
- Before using that result, we need to rule out a synthesis artifact where some
  requested GEMM modules are disconnected and optimized away.
- The retained physical metrics currently leave `stdcell_count`,
  `stdcell_area_um2`, and `instance_area_um2` blank for recent rows.

## Evaluation Scope
- Re-run the current cmp33 mode-compare sweep for:
  - `nm1`
  - `nm2`
  - `nm4`
  - `nm8`
  - `nm16`
- Preserve timing, power, placed area, stdcell area, and stdcell count in each
  metrics row.
- Compare cell/area scaling against requested `compute.gemm.num_modules`.

## Direction Gate
- status: approved
- approved_by: `user`
- approved_utc: `2026-05-21T00:00:00Z`
- note: User identified gate-count scaling as the first suspicion to resolve.
