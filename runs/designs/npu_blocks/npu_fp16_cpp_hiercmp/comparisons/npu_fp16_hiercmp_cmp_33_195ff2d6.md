# Mode Compare: npu_fp16_cpp_hiercmp (nangate45)

- compare_group: `195ff2d6`
- make_target: `3_3_place_gp`
- base_params: `{"CLOCK_PERIOD": 10.0, "CORE_AREA": "50 50 1450 1450", "DIE_AREA": "0 0 1500 1500", "FLOW_VARIANT": "cmp33", "PLACE_DENSITY": 0.4, "SYNTH_KEEP_MODULES": "gemm_compute_array", "TAG": "npu_fp16_hiercmp_cmp_33"}`

| mode | use_macro | status | tag | critical_path_ns | d_cp_ns | die_area_um2 | d_area_um2 | total_power_mw | d_power_mw | macro_manifest | missing_blackboxes | result_json |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| flat_nomacro | no | ok | npu_fp16_hiercmp_cmp_33_flat_nomacro | 5.7013 | +0.0000 | 2250000.0000 | +0.0000 | 0.2104 | +0.0000 |  |  | runs/designs/npu_blocks/npu_fp16_cpp_hiercmp/work/77d647dd/result.json |
| hier_macro | yes | ok | npu_fp16_hiercmp_cmp_33_hier_macro | 5.7409 | +0.0396 | 2250000.0000 | +0.0000 | 0.2128 | +0.0024 | runs/designs/npu_macros/gemm_compute_array_fp16_2slot_c300/macro_manifest.json |  | runs/designs/npu_blocks/npu_fp16_cpp_hiercmp/work/1abd4a06/result.json |
