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

## Test coverage

### Perf unit tests (`npu/sim/perf/tests`)

- `test_perf_basic.py`
  - Runs `run.py` on `minimal_descriptors.bin` in overlap mode.
  - Checks op counts (`DMA_COPY`, `GEMM`, events), total bytes, and overlap timing bounds.
  - Verifies GEMM functional expectation fields are emitted: `expected_dot`, `expected_cycles`, `expected_accum`, `lanes`.
- `test_perf_vec_softmax.py`
  - Builds a synthetic stream with `VEC_OP(add)`, `VEC_OP(dsoftmax)`, and `SOFTMAX`.
  - Checks op decode/order, op counts, total bytes, and non-zero durations.
  - Verifies VEC functional expectation fields are emitted: `expected_result`, `expected_result_bytes`, `lanes`.
- `test_perf_vec_fp16.py`
  - Builds a synthetic fp16 `VEC_OP` stream (`add`, `mul`, `relu`, `gelu`, `softmax`, `layernorm`) using dtype code `fp16`.
  - Verifies fp16 VEC expectation decode for 4x16b lanes packed into 8 result bytes.
  - Confirms deterministic expected-result words for each op.
- `test_perf_gemm_int16.py`
  - Builds a synthetic int16 GEMM descriptor payload and runs with `gemm_mac_type=int16`.
  - Verifies int16 functional expectations (`expected_dot`, `expected_cycles`, `expected_accum`, `lanes`) are decoded correctly.
- `test_perf_gemm_fp16.py`
  - Builds a synthetic fp16 GEMM descriptor payload and runs with `gemm_mac_type=fp16`.
  - Verifies both fp16 modes:
    - builtin raw16 placeholder (`raw16_placeholder`, `int32` accumulation)
    - IEEE-half lane-1 path (`ieee_half`, `fp16` accumulation)
  - Checks fp16 expectation fields including `expected_accum_fp16_hex` for IEEE-half mode.

### RTL/perf integrated regression (`npu/sim/run_golden.sh`)

- Generates mixed + GEMM schedules and runs both RTL and perf simulation.
- Runs functional cross-check:
  - `compare_compute_results.py` compares RTL `GEMM_TIMING accum=` with perf `expected_accum`.
  - `compare_compute_results.py` compares RTL `VEC_DONE result=` with perf `expected_result`.
- Runs timing cross-check:
  - `compare_gemm_timing.py` compares RTL GEMM cycles vs perf GEMM latency model.
  - `golden_gemm_v2_ooo` additionally checks out-of-order completion behavior (`--require-order-change`).
- Includes dedicated fp16 regressions for:
  - builtin fp16 placeholder path
  - C++ RTLGen fp16 `fp_mac` path (IEEE-half, lane-1), when FloPoCo is available
  - C++ RTLGen fp16 VEC path (`add/mul/relu/gelu/softmax/layernorm`, dtype `fp16`), when FloPoCo is available
- Mixed golden schedule also checks VEC regression constraints (`vec_ops=3`, op order `add,mul,relu`, no unknown ops).

### Current coverage boundaries

- Functional compute checking is implemented for int8/int16 GEMM, VEC ops, and fp16 GEMM policy paths.
- fp16 coverage currently includes GEMM lane-1 IEEE-half + raw16 placeholder modes and fp16 VEC (`add/mul/relu/gelu/softmax/layernorm`) expectation decode.
- bf16/fp8 and extended fp16 derivative-vector numeric equivalence are not covered yet.
- No large randomized descriptor fuzzing is included yet.

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
- `vec_lanes` (functional expectation width for VEC result comparison; default follows `gemm_mac_lanes` or `8`)
- `vec_op_costs` (mapping `{op_name: cost}`), used in compute-time estimate
- `vec_dtype_bytes` (fallback when dtype code is unknown)
- `softmax_tops`, `softmax_in_bw_gbps`, `softmax_out_bw_gbps`
- `softmax_overhead_ns`, `softmax_row_overhead_ns`, `softmax_op_cost`
- `softmax_dtype_bytes` (fallback when dtype code is unknown)

### Optional GEMM functional knobs

- `gemm_mac_type` (`int8`, `int16`, or `fp16`) for functional expected-result decode
- `gemm_mac_lanes` (functional expectation lane count; defaults by type: `int8->8`, `int16/fp16->4`)
- fp16 policy lock knobs (used when `gemm_mac_type=fp16`):
  - `gemm_fp16_semantics` (`raw16_placeholder` or `ieee_half`)
  - `gemm_fp16_accumulation` (`int32`, `fp32`, or `fp16`)
  - `gemm_fp16_rounding` (`rne`)
  - `gemm_fp16_subnormals` (`preserve` or `flush`)

Preset configs for golden/perf comparison:
- `npu/sim/perf/example_config_cpp_mac.json` for C++ MAC backend lane-1 path
- `npu/sim/perf/example_config_int16.json` for builtin int16 GEMM path
- `npu/sim/perf/example_config_fp16.json` for builtin fp16 GEMM bring-up path
- `npu/sim/perf/example_config_fp16_cpp.json` for C++ fp16 GEMM backend path
- `npu/sim/perf/example_config_vec_fp16_cpp.json` for C++ fp16 VEC backend path

Current fp16 note:
- Builtin fp16 path is locked to:
  - `gemm_fp16_semantics=raw16_placeholder`
  - `gemm_fp16_accumulation=int32`
  - `gemm_fp16_rounding=rne`
  - `gemm_fp16_subnormals=preserve`
- C++ fp16 GEMM path is locked to:
  - `gemm_fp16_semantics=ieee_half`
  - `gemm_fp16_accumulation=fp16`
  - `gemm_fp16_rounding=rne`
  - `gemm_fp16_subnormals=preserve`
  - `gemm_mac_lanes=1`
