# Performance Simulation (Abstract)

## Purpose
This folder provides a lightweight performance simulator that consumes the
binary descriptor stream and emits a JSON timing trace.

## Inputs
- Binary descriptor stream from `npu/mapper/run.py --out-bin`
- Optional model config JSON (DMA bandwidth, GEMM throughput, overheads)
- Optional SRAM model inputs (arch + CACTI metrics) for DMA/SRAM bandwidth limits

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
make -f npu/sim/perf/Makefile test
```

## Notes
- The v0.1 model supports sequential or overlapped scheduling and handles
  DMA_COPY, GEMM, EVENT_SIGNAL, EVENT_WAIT, and NOOP.
- If `sram_arch_yaml` is provided, DMA_COPY bandwidth can be limited by SRAM
  access time from CACTI metrics (per-instance or max access time).
- `sram_metrics_json` may point to `runs/designs/sram/<id>/sram_metrics.json`
  (preferred) or a summary file with `max_access_time_ns`.

### Example SRAM config (optional)
```json
{
  "dma_bw_gbps": 16.0,
  "gemm_tops": 2.0,
  "event_overhead_ns": 50.0,
  "noop_overhead_ns": 10.0,
  "issue_overhead_ns": 0.0,
  "sram_arch_yaml": "npu/arch/examples/minimal.yml",
  "sram_metrics_json": "runs/designs/sram/minimal/sram_metrics.json"
}
```

See `npu/sim/perf/example_config_sram.json` for a ready-to-run sample.
- Unsupported opcodes are reported as warnings and treated as zero-cost.
- EVENT_SIGNAL with IRQ flag is counted in the summary (`irq_events`).
