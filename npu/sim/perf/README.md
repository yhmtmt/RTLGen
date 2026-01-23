# Performance Simulation (Abstract)

## Purpose
This folder provides a lightweight performance simulator that consumes the
binary descriptor stream and emits a JSON timing trace.

## Inputs
- Binary descriptor stream from `npu/mapper/run.py --out-bin`
- Optional model config JSON (DMA bandwidth, GEMM throughput, overheads)

## Outputs
- JSON trace with per-descriptor start/end timestamps
- Summary metrics (total time, bytes moved, op counts)

## Quick start
```sh
python3 npu/sim/perf/run.py \
  --bin npu/mapper/examples/minimal_descriptors.bin \
  --out /tmp/npu_perf_trace.json \
  --config npu/sim/perf/example_config.json \
  --summary \
  --overlap

make -f npu/sim/perf/Makefile run
```

## Notes
- The v0.1 model supports sequential or overlapped scheduling and handles
  DMA_COPY, GEMM, EVENT_SIGNAL, EVENT_WAIT, and NOOP.
- Unsupported opcodes are reported as warnings and treated as zero-cost.
