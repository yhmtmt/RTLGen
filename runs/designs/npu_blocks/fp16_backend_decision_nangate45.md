# FP16 Backend Sweep (nangate45)

## Inputs
- sweep: `npu/synth/fp16_backend_sweep_nangate45.json`
- make target: `full_flow`
- compared backends: `builtin_raw16`, `cpp_ieee`

## Latest Metrics
| backend | eligible_default | status | tag | critical_path_ns | die_area_um2 | total_power_mw | result_path | notes |
|---|---|---|---|---:|---:|---:|---|---|
| builtin_raw16 | no | ok | npu_fp16_5d34f219 | 5.4287 | 2250000.0000 | 0.2330 | /orfs/flow/reports/nangate45/npu_fp16_builtin_l1/base/6_finish.rpt | non-IEEE placeholder; excluded from default lock |
| cpp_ieee | yes | ok | fp16_cmp_flat_big_gp_37c9f4f3 | 5.7678 | 4840000.0000 | 0.2042 | /orfs/flow/logs/nangate45/npu_fp16_cpp_l1/cmp_flat_big_gp/3_3_place_gp.json |  |

## Recommendation
- Recommended default backend: `cpp_ieee` (lowest `critical_path_ns * die_area * total_power_mw` among default-eligible backends).
