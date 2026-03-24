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
- `docs/developer_loop/prop_l1_npu_nm1_tanh_vec_enable_v1/implementation_summary.md`

## Local Validation
- `python3 -m py_compile npu/rtlgen/gen.py npu/sim/perf/run.py tests/test_npu_rtlgen_vec_tanh.py npu/sim/perf/tests/test_perf_vec_tanh.py`
- `python3 npu/sim/perf/tests/test_perf_vec_tanh.py`
- `python3 tests/test_npu_rtlgen_vec_tanh.py`
- `python3 npu/rtlgen/gen.py --config runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/config_nm1_tanhproxy.json --out runs/designs/npu_blocks/npu_fp16_cpp_nm1_tanhproxy/verilog`

## Next Step
- commit and push this integrated tanh-enable implementation
- queue `l1_prop_l1_npu_nm1_tanh_vec_enable_v1_r1` against the reduced proxy config and first-pass sweep
