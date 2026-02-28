# Mode Compare: npu_fp16_cpp_nm1_cmp (nangate45)

- compare_group: `baed737c`
- make_target: `3_3_place_gp`
- base_params: `{"CLOCK_PERIOD": 10.0, "CORE_AREA": "50 50 1450 1450", "DIE_AREA": "0 0 1500 1500", "FLOW_VARIANT": "nm1_cmp33", "PLACE_DENSITY": 0.4, "SYNTH_KEEP_MODULES": "gemm_compute_array", "TAG": "npu_fp16_nm1_cmp33"}`

## Summary (Mean +/- Stddev)

| mode | use_macro | ok/total | cp_mean_ns | cp_std_ns | d_cp_mean_ns | die_area_mean_um2 | die_area_std_um2 | d_area_mean_um2 | power_mean_mw | power_std_mw | d_power_mean_mw | flow_time_mean_s | flow_time_std_s | d_flow_time_mean_s | stage_time_mean_s | stage_time_std_s | d_stage_time_mean_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat_nomacro | no | 5/5 | 5.5570 | 0.0000 | +0.0000 | 2250000.0000 | 0.0000 | +0.0000 | 0.1931 | 0.0000 | +0.0000 | 848.4180 | 8.3281 | +0.0000 | 424.7380 | 5.2485 | +0.0000 |
| hier_macro | yes | 5/5 | 5.7749 | 0.0000 | +0.2179 | 2250000.0000 | 0.0000 | +0.0000 | 0.1974 | 0.0000 | +0.0043 | 978.8940 | 3.6137 | +130.4760 | 480.1040 | 2.7269 | +55.3660 |

## Per-Run Results

| mode | repeat | use_macro | status | tag | critical_path_ns | d_cp_ns | die_area_um2 | d_area_um2 | total_power_mw | d_power_mw | flow_time_s | d_flow_time_s | stage_time_s | d_stage_time_s | macro_manifest | missing_blackboxes | result_json |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| flat_nomacro | 1 | no | ok | npu_fp16_nm1_cmp33_flat_nomacro_r1 | 5.5570 | +0.0000 | 2250000.0000 | +0.0000 | 0.1931 | +0.0000 | 834.9900 | +0.0000 | 416.7800 | +0.0000 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/3e84d92b/result.json |
| flat_nomacro | 2 | no | ok | npu_fp16_nm1_cmp33_flat_nomacro_r2 | 5.5570 | +0.0000 | 2250000.0000 | +0.0000 | 0.1931 | +0.0000 | 845.7000 | +10.7100 | 422.1000 | +5.3200 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/13a2c990/result.json |
| flat_nomacro | 3 | no | ok | npu_fp16_nm1_cmp33_flat_nomacro_r3 | 5.5570 | +0.0000 | 2250000.0000 | +0.0000 | 0.1931 | +0.0000 | 853.0300 | +18.0400 | 427.2000 | +10.4200 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/34eeb6e5/result.json |
| flat_nomacro | 4 | no | ok | npu_fp16_nm1_cmp33_flat_nomacro_r4 | 5.5570 | +0.0000 | 2250000.0000 | +0.0000 | 0.1931 | +0.0000 | 853.2000 | +18.2100 | 428.1900 | +11.4100 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/439adb1e/result.json |
| flat_nomacro | 5 | no | ok | npu_fp16_nm1_cmp33_flat_nomacro_r5 | 5.5570 | +0.0000 | 2250000.0000 | +0.0000 | 0.1931 | +0.0000 | 855.1700 | +20.1800 | 429.4200 | +12.6400 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/936b2a7b/result.json |
| hier_macro | 1 | yes | ok | npu_fp16_nm1_cmp33_hier_macro_r1 | 5.7749 | +0.2179 | 2250000.0000 | +0.0000 | 0.1974 | +0.0043 | 974.5800 | +139.5900 | 477.8000 | +61.0200 | runs/designs/npu_macros/gemm_compute_array_fp16_nm1_c250/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/54a235ae/result.json |
| hier_macro | 2 | yes | ok | npu_fp16_nm1_cmp33_hier_macro_r2 | 5.7749 | +0.2179 | 2250000.0000 | +0.0000 | 0.1974 | +0.0043 | 977.0800 | +142.0900 | 477.8300 | +61.0500 | runs/designs/npu_macros/gemm_compute_array_fp16_nm1_c250/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/f190a078/result.json |
| hier_macro | 3 | yes | ok | npu_fp16_nm1_cmp33_hier_macro_r3 | 5.7749 | +0.2179 | 2250000.0000 | +0.0000 | 0.1974 | +0.0043 | 978.9600 | +143.9700 | 480.1300 | +63.3500 | runs/designs/npu_macros/gemm_compute_array_fp16_nm1_c250/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/b874bef7/result.json |
| hier_macro | 4 | yes | ok | npu_fp16_nm1_cmp33_hier_macro_r4 | 5.7749 | +0.2179 | 2250000.0000 | +0.0000 | 0.1974 | +0.0043 | 979.4800 | +144.4900 | 480.2700 | +63.4900 | runs/designs/npu_macros/gemm_compute_array_fp16_nm1_c250/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/3a650f98/result.json |
| hier_macro | 5 | yes | ok | npu_fp16_nm1_cmp33_hier_macro_r5 | 5.7749 | +0.2179 | 2250000.0000 | +0.0000 | 0.1974 | +0.0043 | 984.3700 | +149.3800 | 484.4900 | +67.7100 | runs/designs/npu_macros/gemm_compute_array_fp16_nm1_c250/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_nm1_cmp/work/3fa4f194/result.json |
