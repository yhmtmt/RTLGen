# NPU Simulation Report (Draft)

## Purpose
This document will define the standardized metrics and report format for NPU
simulation runs.

Topics to cover:
- End-to-end latency (prefill, decode)
- Throughput (tokens/s, images/s)
- Resource utilization breakdowns
- Memory bandwidth and stall analysis
- Summary JSON schema for dashboards

## v0.1 Trace JSON (performance simulator)
The performance simulator emits a single JSON file with a `trace` array and
summary `stats`. Example schema:

```json
{
  "meta": {
    "version": "0.1",
    "source_bin": "path/to/descriptors.bin"
  },
  "stats": {
    "total_time_ns": 1234.0,
    "total_bytes": 8192,
    "dma_ops": 1,
    "gemm_ops": 1,
    "event_ops": 2,
    "noop_ops": 0,
    "unknown_ops": 0,
    "dma_time_ns": 512.0,
    "gemm_time_ns": 600.0,
    "event_time_ns": 100.0,
    "noop_time_ns": 0.0,
    "unknown_time_ns": 0.0
  },
  "warnings": [],
  "trace": [
    {
      "offset": 0,
      "opcode": 1,
      "name": "DMA_COPY",
      "bytes": 8192,
      "achieved_gbps": 16.0,
      "start_ns": 0.0,
      "end_ns": 512.0
    }
  ]
}
```

Trace entries are sequential in v0.1 (no overlap). Future revisions may add
per-engine timelines for DMA/compute overlap.

Status:
- RTL functional simulation is implemented; performance simulator is in progress.

## Next steps
- Define JSON schema and metrics fields for analytical simulation.
