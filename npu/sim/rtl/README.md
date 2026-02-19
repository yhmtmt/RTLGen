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
  - C++ int8 activation-unit GELU regression (`minimal_cpp_mac.json` + synthetic GELU descriptors)
- These RTL runs are consumed by perf comparison scripts for:
  - GEMM timing consistency (`compare_gemm_timing.py`)
  - GEMM/VEC computation consistency (`compare_compute_results.py`)

## Current coverage boundaries

- Datapath validation covers int8/int16 GEMM, VEC ops, and fp16 GEMM policy paths used in golden flows.
- Floating-point coverage includes fp16 GEMM (builtin placeholder and C++ IEEE-half lane-1) and fp16 VEC (`add/mul/relu/gelu/softmax/layernorm/drelu/dgelu/dsoftmax/dlayernorm`) via RTL/perf compare.
- C++ activation-unit coverage includes int8 GELU path under `activation_source=rtlgen_cpp`.
- bf16/fp8 and constrained-random fp16 derivative-vector numeric stress are not covered yet.
- No constrained-random stress regression is included yet.

## Notes
- AXI memory model is shared in `npu/sim/rtl/axi_mem_model.sv` and used by all RTL testbenches.
