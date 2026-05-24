# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_npu_fp16_compute_parallelism_gate_count_audit_v1`
- active candidate: `l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1_r5`
- retracted candidate: `l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1_r2`

## Revision
- reason: `wrong_configuration`
- detail: the earlier gate-count audit was run before the NPU GEMM/VEC output path was connected through architectural writeback, so physical optimization could remove or underrepresent compute logic.
- replacement run: `l1_npu_fp16_compute_parallelism_gate_count_audit_nm1_nm2_nm4_nm8_nm16_v1_r5_run_05db7eaa0e146670`
- source commit: `62c19c19f91d0d2ec978bc64a2a1cdc625fe403a`
- execution result: `13/13 commands succeeded`
- validation: `scripts/validate_runs.py --skip_eval_queue` passed

## Revised Measurements

| design | mode | status | critical_path_ns | total_power_mw | stdcell_count | instance_area_um2 |
|---|---|---:|---:|---:|---:|---:|
| `nm1` | flat | `ok` | 5.9276 | 0.310 | 252539 | 566529 |
| `nm1` | hier | `ok` | 6.1529 | 0.323 | 252279 | 565977 |
| `nm2` | flat | `ok` | 5.9136 | 0.218 | 255723 | 571595 |
| `nm2` | hier | `ok` | 5.9211 | 0.340 | 256208 | 572005 |
| `nm4` | flat | `ok` | 5.9724 | 0.502 | 262985 | 582822 |
| `nm4` | hier | `ok` | 6.3871 | 0.459 | 263267 | 583087 |
| `nm8` | flat | `ok` | 5.9453 | 0.716 | 276756 | 604460 |
| `nm8` | hier | `flow_failed` |  |  |  |  |
| `nm16` | flat | `ok` | 6.1518 | 1.200 | 304064 | 647381 |
| `nm16` | hier | `ok` | 6.2277 | 1.070 | 304482 | 647410 |

## Interpretation
- The prior r2 decision is removed from the active decision path.
- The corrected r5 data shows retained stdcell count and instance area increasing with requested module count, so the missing-output-connection concern is resolved for the active evidence.
- The earlier optimistic nm4 flat timing remains visible but is no longer accompanied by unusually low power; under corrected connectivity, nm4 flat is 0.502 mW and nm8/nm16 continue to increase in power and cell count.
- `nm8` hierarchical macro mode remains infeasible in this flow point and should be treated as a flow boundary, not as an architecture win or loss.

## Recommendation
- `promote`
- Use r5 as the active Layer 1 physical evidence for compute-parallelism scaling.
- Exclude r2 and any pre-writeback-fix NPU compute-parallelism measurements from ranking, baseline selection, and follow-on architecture decisions unless explicitly shown as audit history.
