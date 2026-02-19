# RTL Simulation

## Purpose
This folder provides Verilog testbenches for generated NPU top RTL and AXI-Lite wrapper RTL.
The tests validate descriptor execution behavior, MMIO/IRQ flow, and AXI memory movement.

## Inputs
- Binary descriptor stream from `npu/mapper/run.py --out-bin`

## Quick commands
- `make -f npu/sim/rtl/Makefile run`
- `make -f npu/sim/rtl/Makefile run BYTES=8192`
- `make -f npu/sim/rtl/Makefile run BIN=npu/sim/rtl/golden_descriptors.bin BYTES=4096 VVPFLAGS="+gemm_mem_test=256 +gemm_mac_test=1"`
- `make -f npu/sim/rtl/Makefile run VVPFLAGS="+vec_test=1"`
- `make -f npu/sim/rtl/Makefile run VVPFLAGS="+vec_test=1 +vec_ext_test=1"`
- `make -f npu/sim/rtl/Makefile run-axi`
- `make -f npu/sim/rtl/Makefile run-axi-multi`

## Test coverage

### `tb_npu_shell.sv` coverage

- MMIO control path:
  - CQ programming (`CQ_BASE`, `CQ_SIZE`, `CQ_TAIL`, `DOORBELL`)
  - CQ progress (`CQ_HEAD == CQ_TAIL`)
  - IRQ status behavior (`CQ_EMPTY`, event IRQ)
- DMA behavior:
  - Descriptor decode/handshake (`src`, `dst`, `bytes`)
  - End-to-end memory data check for DMA copy path
  - SRAM path check (`+sram_test=1`): mem->SRAM->mem copy round trip
- GEMM behavior:
  - Descriptor scan + completion accounting for all GEMM descriptors
  - Per-descriptor expected accumulation check (`+gemm_mac_test=1`)
  - Completion timing log with stable identifiers (`GEMM_TIMING ... offset=... cycles=... accum=...`)
- VEC behavior:
  - Per-descriptor completion accounting and per-lane expected value checks
  - In-testbench per-lane value checks currently apply to `dtype=int8`; non-int8 vectors are validated through RTL/perf cross-check (`compare_compute_results.py`)
  - Default vector tests (`+vec_test=1`) cover `relu`, `add`, `mul` and optional `gelu` mode (`+vec_gelu_test=1`)
  - Extended vector tests (`+vec_test=1 +vec_ext_test=1`) add `softmax`, `layernorm`, `drelu`, `dgelu`, `dsoftmax`, `dlayernorm`
  - Completion log includes final vector output (`VEC_DONE ... result=0x...`)

### AXI-Lite wrapper coverage

- `tb_axi_lite_mmio.sv`:
  - AXI-Lite register access and single-stream submit flow
  - DMA request and memory result check for default/sram modes
- `tb_axi_lite_multi.sv`:
  - Multi-descriptor submit flow and CQ/IRQ behavior
  - DMA request count expectations and memory data checks

### Golden regression coverage

- `npu/sim/run_golden.sh` runs mixed/GEMM schedules across multiple backend configs:
  - mixed (`golden_descriptors.bin`)
  - GEMM v2 single (`golden_gemm_v2_descriptors.bin`)
  - GEMM v2 two-op (`golden_gemm_v2_two_descriptors.bin`)
  - GEMM v2 out-of-order (`golden_gemm_v2_ooo_descriptors.bin`)
  - C++ int8 MAC backend (`minimal_cpp_mac.json`)
  - builtin int16 backend (`minimal_int16.json`)
  - builtin fp16 placeholder backend (`minimal_fp16.json`)
  - C++ fp16 IEEE-half backend (`minimal_fp16_cpp.json`) when FloPoCo is available
  - C++ fp16 VEC backend (`minimal_vec_fp16_cpp.json`) when FloPoCo is available
  - C++ fp16 activation-wired VEC backend (`minimal_vec_fp16_act_cpp.json`) when FloPoCo is available
  - C++ fp16 edge GEMM regression (`golden_fp16_edge_gemm_descriptors.bin`) when FloPoCo is available
  - C++ fp16 edge VEC regression (`golden_vec_fp16_edge_descriptors.bin`, ops `add/mul/relu`) when FloPoCo is available
  - C++ int8 activation-unit suite regression (`minimal_cpp_mac.json` + synthetic activation descriptors)
  - C++ fp16 activation-unit standalone smoke regression (`minimal_vec_act_fp16_cpp.json` + `tb_cpp_vec_act_fp16_smoke.sv`)
- These RTL runs are consumed by perf comparison scripts for:
  - GEMM timing consistency (`compare_gemm_timing.py`)
  - GEMM/VEC computation consistency (`compare_compute_results.py`)

## Current coverage boundaries

- Datapath validation covers int8/int16 GEMM, VEC ops, and fp16 GEMM policy paths used in golden flows.
- Floating-point coverage includes fp16 GEMM (builtin placeholder and C++ IEEE-half lane-1) and fp16 VEC (`add/mul/relu/gelu/softmax/layernorm/drelu/dgelu/dsoftmax/dlayernorm`) via RTL/perf compare.
- Directed fp16 edge-case RTL/perf parity is covered for C++ fp16 GEMM/VEC (signed-zero, subnormal, Inf, and ReLU NaN pass-through) in FloPoCo-enabled runs.
- GEMM NaN edge behavior for the C++ fp16 backend is not yet locked as a strict parity gate; it remains under characterization.
- C++ activation-unit coverage includes int8 activation suite path under `activation_source=rtlgen_cpp`.
- C++ fp16 activation coverage includes both activation-wired fp16 VEC regression and standalone module smoke checks.
- bf16/fp8 and constrained-random fp16 derivative-vector numeric stress are not covered yet.
- No constrained-random stress regression is included yet.

## Notes
- AXI memory model is shared in `npu/sim/rtl/axi_mem_model.sv` and used by all RTL testbenches.
