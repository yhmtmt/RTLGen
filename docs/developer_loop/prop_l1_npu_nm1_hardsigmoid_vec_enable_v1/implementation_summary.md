# Implementation Summary

## Proposal
- `proposal_id`: `prop_l1_npu_nm1_hardsigmoid_vec_enable_v1`
- `title`: `NPU nm1 hard-sigmoid vec enable`

## Scope
- integrated bounded `int8` hard-sigmoid support added to the fixed `nm1` vec path
- reduced integrated physical proxy added so the first remote item can target a practical `architecture_block` source instead of full `npu_top`
- this follows the accepted sigmoid/tanh pattern: integrated legality/generation first, reduced physical source next, Layer 2 later

## Files Changed
- `npu/rtlgen/gen.py`
- `npu/rtlgen/config_spec.md`
- `npu/sim/perf/model.py`
- `npu/sim/perf/run.py`
- `tests/test_npu_rtlgen_vec_hardsigmoid.py`
- `npu/sim/perf/tests/test_perf_vec_hardsigmoid.py`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidcmp/config_nm1_hardsigmoid.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidcmp/README.md`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidproxy/config_nm1_hardsigmoidproxy.json`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidproxy/README.md`
- `runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidproxy/sweep_proxy_firstpass.json`
- `docs/developer_loop/prop_l1_npu_nm1_hardsigmoid_vec_enable_v1/implementation_summary.md`
- `docs/developer_loop/prop_l1_npu_nm1_hardsigmoid_vec_enable_v1/evaluation_requests.json`

## Local Validation
- `python3 -m py_compile npu/rtlgen/gen.py npu/sim/perf/model.py npu/sim/perf/run.py tests/test_npu_rtlgen_vec_hardsigmoid.py npu/sim/perf/tests/test_perf_vec_hardsigmoid.py`
- `python3 npu/sim/perf/tests/test_perf_vec_hardsigmoid.py`
- `python3 tests/test_npu_rtlgen_vec_hardsigmoid.py`
- `python3 npu/rtlgen/gen.py --config runs/designs/npu_blocks/npu_fp16_cpp_nm1_hardsigmoidproxy/config_nm1_hardsigmoidproxy.json --out /tmp/nm1_hardsigmoidproxy_out`

## Remote Evaluation
- pushed implementation commit: `cbb20620f15f8cff516dda5bee938f328f2e0d3c`
- queued first remote evidence item:
  - DB item `l1_prop_l1_npu_nm1_hardsigmoid_vec_enable_v1_r1`
  - current DB state at queue-record time: `LEASED`
  - objective: `npu_nm1_hardsigmoid_vec_physical_metrics`

## Next Step
- let `r1` finish and review the resulting reduced-proxy evidence PR
