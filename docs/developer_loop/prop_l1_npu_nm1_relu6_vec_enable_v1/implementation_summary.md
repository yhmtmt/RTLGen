# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_relu6_vec_enable_v1`
- `title`: `NPU nm1 ReLU6 vec enable`

## Scope
- integrated bounded `int8` ReLU6 support added to the fixed `nm1` vec path
- reduced integrated physical proxy added so the first remote item can target a practical `architecture_block` source instead of full `npu_top`
- this follows the accepted sigmoid/tanh pattern: integrated legality/generation first, reduced physical source next, Layer 2 later

## Files Changed
- `npu/rtlgen/gen.py`
- `npu/rtlgen/config_spec.md`
- `npu/sim/perf/model.py`
- `npu/sim/perf/run.py`
- `tests/test_npu_rtlgen_vec_relu6.py`
- `npu/sim/perf/tests/test_perf_vec_relu6.py`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6cmp/config_nm1_relu6.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6cmp/README.md`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6cmp/sweep_hier_firstpass.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6proxy/config_nm1_relu6proxy.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6proxy/README.md`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6proxy/sweep_proxy_firstpass.json`
- `docs/developer_loop/prop_l1_npu_nm1_relu6_vec_enable_v1/implementation_summary.md`
- `docs/developer_loop/prop_l1_npu_nm1_relu6_vec_enable_v1/evaluation_requests.json`

## Local Validation
- `python3 -m py_compile npu/rtlgen/gen.py npu/sim/perf/model.py npu/sim/perf/run.py tests/test_npu_rtlgen_vec_relu6.py npu/sim/perf/tests/test_perf_vec_relu6.py`
- `python3 npu/sim/perf/tests/test_perf_vec_relu6.py`
- `python3 tests/test_npu_rtlgen_vec_relu6.py`
- `python3 npu/rtlgen/gen.py --config runs/designs/npu_blocks/npu_fp16_cpp_nm1_relu6proxy/config_nm1_relu6proxy.json --out /tmp/nm1_relu6proxy_out`

## Remote Evaluation
- pushed implementation commit: `cbb20620f15f8cff516dda5bee938f328f2e0d3c`
- queued first remote evidence item:
  - DB item `l1_prop_l1_npu_nm1_relu6_vec_enable_v1_r1`
  - current DB state at queue-record time: `LEASED`
  - objective: `npu_nm1_relu6_vec_physical_metrics`

## Next Step
- let `r1` finish and review the resulting reduced-proxy evidence PR
