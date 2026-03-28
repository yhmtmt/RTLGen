# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_tanh_vec_enable_v1`
- `title`: `NPU nm1 tanh vec enable`

## Scope
- integrated bounded `int8` tanh support added to the fixed `nm1` vec path
- reduced integrated physical proxy added so the first remote item can target a practical `architecture_block` source instead of full `npu_top`
- this follows the accepted sigmoid pattern: integrated legality/generation first, reduced physical source next, Layer 2 later

## Files Changed
- `npu/rtlgen/gen.py`
- `npu/sim/perf/run.py`
- `npu/sim/perf/model.py`
- `tests/test_npu_rtlgen_vec_tanh.py`
- `npu/sim/perf/tests/test_perf_vec_tanh.py`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhcmp/config_nm1_tanh.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhcmp/README.md`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/config_nm1_tanhproxy.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/README.md`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/sweep_proxy_firstpass.json`
- `docs/proposals/prop_l1_npu_nm1_tanh_vec_enable_v1/implementation_summary.md`
- `docs/proposals/prop_l1_npu_nm1_tanh_vec_enable_v1/evaluation_requests.json`

## Local Validation
- `python3 -m py_compile npu/rtlgen/gen.py npu/sim/perf/run.py tests/test_npu_rtlgen_vec_tanh.py npu/sim/perf/tests/test_perf_vec_tanh.py`
- `python3 npu/sim/perf/tests/test_perf_vec_tanh.py`
- `python3 tests/test_npu_rtlgen_vec_tanh.py`
- `python3 npu/rtlgen/gen.py --config runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/config_nm1_tanhproxy.json --out runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/verilog`

## Remote Evaluation
- pushed implementation commit: `63f003accd22559c6bd0200b2adfcd9b5873f6f3`
- initial queue attempt `r1` failed only because of an incorrect full SHA
- accepted remote evidence:
  - PR `#81`
  - DB item `l1_prop_l1_npu_nm1_tanh_vec_enable_v1_r2`
  - accepted best point:
    - `param_hash`: `bf5fc187`
    - `critical_path_ns`: `2.8082`
    - `die_area`: `1440000.0`
    - `total_power_mw`: `0.000358`

## Next Step
- seed the next bounded Layer 2 tanh direct-output work against the accepted reduced tanh architecture-block source
