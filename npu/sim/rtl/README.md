# RTL Simulation (Shell Bring-up)

## Purpose
This folder provides a minimal testbench for the generated NPU top module.
It validates the MMIO control path, queue tail/head update, and IRQ behavior.

## Current status
- RTL shell + DMA/AXI path validated for 8KB DMA copy.

Inputs:
- Binary descriptor stream from `npu/mapper/run.py --out-bin`

Notes:
- The current RTL stub **does not execute descriptors**. It only consumes the
  queue on doorbell and raises the CQ_EMPTY IRQ.
- AXI memory model is shared in `npu/sim/rtl/axi_mem_model.sv` and used by both
  testbenches.
- AXI-Lite tests include a single-descriptor stream and a multi-descriptor
  stream (DMA + non-DMA ops).

Quick commands:
- `make -f npu/sim/rtl/Makefile run`
- `make -f npu/sim/rtl/Makefile run BYTES=8192`
- `make -f npu/sim/rtl/Makefile run-axi`
- `make -f npu/sim/rtl/Makefile run-axi-multi`

## Next steps
- Add GEMM/event descriptor checks in the RTL TB.
