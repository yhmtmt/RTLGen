# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_npu_fp16_compute_parallelism_gate_count_audit_v1`
- `title`: `NPU FP16 compute parallelism gate-count audit`

## Checks
- metric:
  - threshold: each metrics row has non-empty `stdcell_count`
- metric:
  - threshold: each metrics row has non-empty `stdcell_area_um2`
- metric:
  - threshold: `stdcell_count` and/or `stdcell_area_um2` increase from nm1 to
    larger module counts unless a documented synthesis explanation is present
- metric:
  - threshold: `config_nmN.json` and retained metrics agree on the requested
    `compute.gemm.num_modules`

## Result
- status: pending
- note: Evaluate after the gate-count audit result is available.
