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
  DMA_COPY, GEMM, VEC_OP, SOFTMAX, EVENT_SIGNAL, EVENT_WAIT, and NOOP.
- If `sram_arch_yaml` is provided, DMA_COPY bandwidth can be limited by SRAM
  access time from CACTI metrics (per-instance or max access time).
- `sram_metrics_json` may point to `runs/designs/sram/<id>/sram_metrics.json`
  (preferred) or a summary file with `max_access_time_ns`.
- VEC op decode uses descriptor `flags` low nibble (`[3:0]`) for op code and
  high nibble (`[7:4]`) for dtype.

### Bandwidth units
All `*_bw_gbps` knobs are interpreted as effective **GB/s** (gigabytes per
second), not Gbit/s.

Implementation detail:
- `time_s = bytes / (bw_gbps * 1e9)`

Practical modeling guidance:
- Use `dma_bw_gbps` for *external* memory traffic (DMA_COPY ops, DRAM-class).
- Use `gemm_in_bw_gbps` / `gemm_out_bw_gbps` for *internal* feed/drain to the
  GEMM engine (e.g., SRAM → compute) if you want to separate DRAM vs on-chip BW.

### DRAM (130nm-era) → HBM sweep presets
If you want a simple bound on "external memory", sweep `dma_bw_gbps`.

Cheatsheet (single 64-bit channel, theoretical peak):
- SDR SDRAM PC133: ~1.066 GB/s
- DDR1 DDR-200/266/333/400: 1.6 / 2.1 / 2.7 / 3.2 GB/s

HBM ballpark (per stack/placement, peak order-of-magnitude):
- HBM3E-class: ~1200 GB/s
- HBM4 JEDEC peak: ~2000 GB/s
- Aggressive ceiling (vendor configs): ~2800 GB/s

Suggested scenario set (effective GB/s):
- Floor (DDR1): 3.2
- Typical (modern DDR-class, placeholder until interface is fixed): 100
- HBM3E: 1200
- HBM4: 2000
- Ceiling: 2800

Note:
- This wide sweep is mainly for Transformer-class workloads. For small MLP
  sanity models, start with a single fixed `dma_bw_gbps` and only add sweeps
  when needed.

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

### Optional VEC / SOFTMAX knobs
You can tune vector op performance with these optional config keys:

- `vec_tops`, `vec_in_bw_gbps`, `vec_out_bw_gbps`, `vec_overhead_ns`
- `vec_op_costs` (mapping `{op_name: cost}`), used in compute-time estimate
- `vec_dtype_bytes` (fallback when dtype code is unknown)
- `softmax_tops`, `softmax_in_bw_gbps`, `softmax_out_bw_gbps`
- `softmax_overhead_ns`, `softmax_row_overhead_ns`, `softmax_op_cost`
- `softmax_dtype_bytes` (fallback when dtype code is unknown)
