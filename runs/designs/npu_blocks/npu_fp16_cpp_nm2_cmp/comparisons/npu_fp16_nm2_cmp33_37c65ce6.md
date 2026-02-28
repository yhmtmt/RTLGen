# Mode Compare: npu_fp16_cpp_nm2_cmp (nangate45)

- compare_group: `37c65ce6`
- make_target: `3_3_place_gp`
- base_params: `{"CLOCK_PERIOD": 10.0, "CORE_AREA": "50 50 1450 1450", "DIE_AREA": "0 0 1500 1500", "FLOW_VARIANT": "nm2_cmp33", "PLACE_DENSITY": 0.4, "SYNTH_KEEP_MODULES": "gemm_compute_array", "TAG": "npu_fp16_nm2_cmp33"}`

## Summary (Mean +/- Stddev)

| mode | use_macro | ok/total | cp_mean_ns | cp_std_ns | d_cp_mean_ns | die_area_mean_um2 | die_area_std_um2 | d_area_mean_um2 | power_mean_mw | power_std_mw | d_power_mean_mw | flow_time_mean_s | flow_time_std_s | d_flow_time_mean_s | stage_time_mean_s | stage_time_std_s | d_stage_time_mean_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat_nomacro | no | 5/5 | 5.7013 | 0.0000 | +0.0000 | 2250000.0000 | 0.0000 | +0.0000 | 0.2104 | 0.0000 | +0.0000 | 829.8140 | 7.1938 | +0.0000 | 415.6120 | 5.3143 | +0.0000 |
| hier_macro | yes | 5/5 | 5.7409 | 0.0000 | +0.0396 | 2250000.0000 | 0.0000 | +0.0000 | 0.2128 | 0.0000 | +0.0024 | 981.7820 | 10.2549 | +151.9680 | 452.3540 | 12.7509 | +36.7420 |

## Per-Run Results

| mode | repeat | use_macro | status | tag | critical_path_ns | d_cp_ns | die_area_um2 | d_area_um2 | total_power_mw | d_power_mw | flow_time_s | d_flow_time_s | stage_time_s | d_stage_time_s | macro_manifest | missing_blackboxes | result_json |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| flat_nomacro | 1 | no | ok | npu_fp16_nm2_cmp33_flat_nomacro_r1 | 5.7013 | +0.0000 | 2250000.0000 | +0.0000 | 0.2104 | +0.0000 | 817.1200 | +0.0000 | 407.6200 | +0.0000 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/258015dc/result.json |
| flat_nomacro | 2 | no | ok | npu_fp16_nm2_cmp33_flat_nomacro_r2 | 5.7013 | +0.0000 | 2250000.0000 | +0.0000 | 0.2104 | +0.0000 | 833.4600 | +16.3400 | 420.8000 | +13.1800 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/95526f98/result.json |
| flat_nomacro | 3 | no | ok | npu_fp16_nm2_cmp33_flat_nomacro_r3 | 5.7013 | +0.0000 | 2250000.0000 | +0.0000 | 0.2104 | +0.0000 | 834.4600 | +17.3400 | 419.7900 | +12.1700 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/099823db/result.json |
| flat_nomacro | 4 | no | ok | npu_fp16_nm2_cmp33_flat_nomacro_r4 | 5.7013 | +0.0000 | 2250000.0000 | +0.0000 | 0.2104 | +0.0000 | 831.2100 | +14.0900 | 413.5500 | +5.9300 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/b276f2e7/result.json |
| flat_nomacro | 5 | no | ok | npu_fp16_nm2_cmp33_flat_nomacro_r5 | 5.7013 | +0.0000 | 2250000.0000 | +0.0000 | 0.2104 | +0.0000 | 832.8200 | +15.7000 | 416.3000 | +8.6800 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/f0b4f9e6/result.json |
| hier_macro | 1 | yes | ok | npu_fp16_nm2_cmp33_hier_macro_r1 | 5.7409 | +0.0396 | 2250000.0000 | +0.0000 | 0.2128 | +0.0024 | 999.8400 | +182.7200 | 474.4900 | +66.8700 | runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/5d0ac971/result.json |
| hier_macro | 2 | yes | ok | npu_fp16_nm2_cmp33_hier_macro_r2 | 5.7409 | +0.0396 | 2250000.0000 | +0.0000 | 0.2128 | +0.0024 | 976.4300 | +159.3100 | 445.2500 | +37.6300 | runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/a9ae3c35/result.json |
| hier_macro | 3 | yes | ok | npu_fp16_nm2_cmp33_hier_macro_r3 | 5.7409 | +0.0396 | 2250000.0000 | +0.0000 | 0.2128 | +0.0024 | 976.6900 | +159.5700 | 445.0800 | +37.4600 | runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/c51fa4a2/result.json |
| hier_macro | 4 | yes | ok | npu_fp16_nm2_cmp33_hier_macro_r4 | 5.7409 | +0.0396 | 2250000.0000 | +0.0000 | 0.2128 | +0.0024 | 975.6300 | +158.5100 | 444.8100 | +37.1900 | runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/98a03366/result.json |
| hier_macro | 5 | yes | ok | npu_fp16_nm2_cmp33_hier_macro_r5 | 5.7409 | +0.0396 | 2250000.0000 | +0.0000 | 0.2128 | +0.0024 | 980.3200 | +163.2000 | 452.1400 | +44.5200 | runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm2_cmp/work/41f8b4a8/result.json |
