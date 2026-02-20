# Simulation Development Plan (RTL + Performance)

## Purpose
This plan defines two simulation schemes:
1) **RTL functional validation** (logic correctness)
2) **Abstracted performance simulation** (GPU-accelerated if available)

## Current status
- RTL functional simulation path is implemented.
- Performance simulation is implemented (analytical v0.1 under `npu/sim/perf/`).
- Process note: re-run RTL simulation whenever `npu/rtlgen/gen.py` changes.
- Mapper golden schedule validates cleanly (`npu/mapper/examples/golden_schedule.yml`).
- Golden mapping sim flow: RTL (Makefile `BIN=`) and perf (`npu/sim/perf/run.py --bin`).
- FP16-2 in progress: C++ `fp_mac` GEMM backend wiring is implemented with lane-1 IEEE-half policy and RTL/perf comparison hooks.
- FP16-3 progressed: fp16 VEC (`add/mul/relu/gelu/softmax/layernorm/drelu/dgelu/dsoftmax/dlayernorm`) path is wired with C++ IEEE `fp_mac` backend and perf/RTL comparison hooks.
- Phase-2 activation kickoff: C++ activation-unit int8 suite (`relu/gelu/softmax/layernorm/drelu/dgelu/dsoftmax/dlayernorm`) is explicitly exercised in golden RTL/perf parity flow (`activation_source=rtlgen_cpp`), and fp16 activation path is now exercised both in wired fp16 VEC regression and standalone smoke checks.
- FP16-4 progressed: directed fp16 edge-case regression coverage now includes zero/signed-zero/subnormal/Inf/NaN in perf unit tests, plus fp16 C++ RTL/perf edge parity legs for GEMM/VEC in golden flow when FloPoCo is available; CI runs perf unit tests before golden simulation.
- FP16-5 progressed: OpenROAD fp16 backend sweep executed at
  `make_target=3_5_place_dp` (`builtin_raw16` vs `cpp_ieee`) with report output
  under `runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`; default
  recommendation is `cpp_ieee` among default-eligible backends
  (`builtin_raw16` is kept as a non-IEEE placeholder baseline).
- FP16-5 lock step completed: fp16 GEMM default backend in RTL generator is
  now `rtlgen_cpp` (IEEE-half path) unless explicitly overridden.
- FP16-5 finish sign-off completed: `make_target=finish` sweep recorded final
  metrics in the same report:
  - `builtin_raw16`: `critical_path_ns=5.4287`, `die_area=2250000`,
    `total_power_mw=0.233`
  - `cpp_ieee`: `critical_path_ns=5.6462`, `die_area=2250000`,
    `total_power_mw=0.229`
  and recommendation remains `cpp_ieee` (default-eligible backend).

## A) RTL Functional Validation (First Priority)

### Goals
- Validate that RTLGen-produced shell + compute RTL responds correctly to
  command descriptors.
- Provide a minimal, repeatable testbench for logic correctness.

### Scope (v0.1)
- MMIO init (CQ base/size, tail, doorbell)
- Command parsing (DMA_COPY, GEMM stub, EVENT_SIGNAL)
- IRQ behavior and status updates
- Optional: memory model hooks for DMA sanity

### Deliverables
- `npu/rtlgen/` generator stub emitting a tiny top module
- `npu/rtlgen/examples/` config(s)
- `npu/sim/rtl/` testbench that:
  - reads `*.bin` descriptors
  - drives MMIO writes and doorbell
  - checks expected status/IRQ/events
 - AXI memory model for DMA validation (shared)

### Suggested steps
1) Define RTLGen NPU config format (JSON/YAML). **Done**
2) Create a **minimal RTL top** with MMIO + CQ + DMA stub. **Done**
3) Build testbenches for MMIO and AXI-Lite. **Done**
4) Run golden command streams through RTL. **Done**

## A.1) Compute Bring-up Plan (GEMM + VEC via RTLGen MAC generators)

### Purpose
- Add a minimal but real compute path so GEMM/VEC are no longer timing-only
  stubs in `npu/rtlgen/out/top.v`.
- Keep compute generation parameterized so future architecture sweeps can
  switch MAC styles without rewriting top-level RTL.

### Scope (initial implementation)
- GEMM: integer MAC array with deterministic accumulate/writeback behavior.
- VEC: minimal elementwise ops (`add`, `mul`, `relu`) using the same MAC
  datapath where possible.
- Phase-2 preference: source activation RTL from C++ `src/rtlgen` where
  available (`relu`, `gelu`, `softmax`, `layernorm`, `drelu`, `dgelu`,
  `dsoftmax`, `dlayernorm`).
- Keep descriptor/IRQ semantics stable with `npu/shell/spec.md`.

### RTLGen extension points
1) Extend config schema with a compute section:
   - `compute.enabled`
   - `compute.gemm.mac_type` (e.g., `int8`, `int16`, `fp16`)
   - `compute.gemm.lanes`, `compute.gemm.accum_width`, `compute.gemm.pipeline`
   - `compute.vec.ops` (allowed op list)
2) Add generator output modules for MAC variants under `npu/rtlgen/`:
   - reusable MAC primitive(s)
   - lane array wrapper
   - GEMM/VEC control wrapper
3) Update top generation:
   - wire descriptor decode to compute issue/complete
   - keep DMA and CQ flow unchanged for compatibility
   - expose a clear fallback path when `compute.enabled=false`

### Validation gates
1) RTL functional:
   - add GEMM correctness checks in `npu/sim/rtl/` (small matrix sanity tests)
   - add VEC op checks for `add/mul/relu/gelu/softmax/layernorm` and
     derivative ops
   - keep existing DMA/CQ regressions green
2) Mapping/perf alignment:
   - mapper emits descriptors that match new compute fields
   - perf sim uses matching op semantics and latency knobs
3) Synthesis readiness:
   - create a dedicated design directory under `runs/designs/npu_blocks/`
     for compute-enabled top
   - run `npu/synth/run_block_sweep.py` on that target (Nangate45 first)

### Delivery phases
1) Phase 1: single MAC type (`int8`) + GEMM correctness in RTL sim.
2) Phase 2: add VEC minimal ops (`add/mul/relu`) on shared datapath.
   - use C++ activation modules as the primary source for supported scalar
     activations where configured (`compute.vec.activation_source=rtlgen_cpp`)
   - keep mapper/perf semantics aligned while adding extended ops
     (`softmax/layernorm` and derivatives)
3) Phase 3: add second MAC type (`int16` or `fp16`) behind config switch.
4) Phase 4: run OpenROAD block sweep and compare against DMA/CQ-only baseline.
5) Phase 5: integrate C++ `src/rtlgen` MAC generator path into NPU MAC-core
   exploration:
   - add `mac` operation config in C++ RTLGen
   - feed accumulator input back into partial-product rows (`pp_row_feedback`)
   - evaluate PPA/timing tradeoffs with the same OpenROAD block sweep flow

## A.2) FP16 Operation Implementation Plan (NPU Compute Path)

### Goal
- Replace the current fp16 placeholder path with a real floating-point
  datapath for GEMM and VEC operations, while keeping descriptor and shell
  behavior stable.

### Current baseline
- `compute.gemm.mac_type=fp16` exists, but current RTL treats lanes as raw
  signed-16 values (placeholder arithmetic).
- C++ RTLGen can emit FloPoCo-backed FP units (`fp_mul`, `fp_add`, `fp_mac`).
  GEMM `fp_mac` is integrated as an optional lane-1 backend (`mac_source=rtlgen_cpp`),
  and fp16 VEC arithmetic/activation routing is integrated behind
  `compute.vec.fp16_arith_source=rtlgen_cpp`.

### Numeric policy to lock first
1) Data format:
   - inputs/outputs in IEEE binary16 bit layout (`wE=5`, `wF=10`).
2) Accumulation:
   - select one path and keep it explicit in config/docs:
     - `fp16_accum` (lower area/latency target), or
     - `fp32_accum` (better numeric stability).
3) Rounding/subnormal behavior:
   - default round-to-nearest-even for generated FP operators.
   - define whether subnormals are preserved or flushed at NPU boundary.
4) Exceptional values:
   - define NaN/Inf propagation expectations for GEMM/VEC compare scripts.

### Architecture and integration steps
1) Backend selection in `npu/rtlgen/gen.py`:
   - add explicit fp16 backend source options (builtin placeholder vs C++ RTLGen
     FP backend) and fail fast on unsupported combinations.
2) Module integration:
   - generate/import fp16 compute units from C++ RTLGen
     (`fp_mac` for GEMM, `fp_add`/`fp_mul` and activation units for VEC path).
   - add wrapper shims if interface encoding differs (FloPoCo FP vs IEEE ports).
3) Lane wrapper/control:
   - support lane-parallel issue with deterministic per-op completion timing.
   - expose latency knobs in config for perf-model alignment.
4) Activation path:
   - route VEC activation ops (`relu`, `gelu`, `softmax`, `layernorm`) through
     standalone generated activation modules when `activation_source=rtlgen_cpp`.

### Verification and sign-off gates
1) Unit tests (module level):
   - directed IEEE half vectors: zero/subnormal/normal/Inf/NaN and sign cases.
   - random differential tests against software reference (`numpy.float16`
     or equivalent deterministic reference model).
2) RTL integration tests:
   - GEMM-only fp16 descriptor regressions.
   - VEC-only fp16 regressions (`add/mul/relu/gelu/softmax/layernorm`).
   - mixed GEMM+VEC schedule regressions with event ordering checks.
3) Perf-model parity:
   - update `npu/sim/perf/run.py` fp16 execution semantics to match chosen
     accumulation and exceptional-value policy.
   - keep `compare_compute_results.py` tolerant to fp roundoff where required.
4) CI:
   - include fp16 golden flow target in `npu/sim/run_golden.sh` and CI workflow.

### PPA and optimization loop
1) Add fp16-enabled design targets under `runs/designs/npu_blocks/`.
2) Run OpenROAD sweeps on fp16 GEMM backends:
   - placeholder builtin
   - C++ RTLGen fp backend(s)
3) Compare timing/area/power vs int8/int16 baselines and feed results back into
   lane count, pipeline depth, and backend selection defaults.

### Delivery phases
1) Phase FP16-1: numeric policy lock + config/schema/doc updates.
2) Phase FP16-2: C++ fp16 GEMM backend wiring (`fp_mac`) + RTL/perf parity.
3) Phase FP16-3: fp16 VEC arithmetic + activation module routing.
4) Phase FP16-4: edge-case compliance regression suite + CI hardening.
5) Phase FP16-5: OpenROAD sweep and backend-default decision.

## B) Abstracted Performance Simulation (Second Priority)

### Goals
- Estimate performance without full RTL timing.
- Enforce NPU constraints while using software/GPU to compute.

### Scope (v0.1)
- Consume binary descriptor stream from `npu/mapper/run.py --out-bin`.
- Use simple cost models (compute + DMA + fixed overheads).
- Emit a JSON timing trace + summary metrics.

### Deliverables
- `npu/sim/perf/model.py`: cost model stubs
- `npu/sim/perf/run.py`: parse descriptor bin + emit JSON trace
- `npu/sim/report.md`: JSON trace schema + summary fields

### Suggested steps
1) Define model parameters (bandwidth/throughput/overheads).
2) Implement analytical simulator (no GPU required).
3) Add optional GPU kernels later for accuracy.

## C) Interfaces Between RTL and Performance Sims
- Shared descriptors (binary) from `npu/mapper/run.py --out-bin`
- Shared config schema (arch + shell + perf model config)
- Shared error/IRQ semantics (from `npu/shell/spec.md`)

## Next steps
- Continue Phase 2 hardening with additional constrained-random VEC parity
  runs for `softmax/layernorm` and derivative ops.
- Continue Phase 5 integration: route C++ RTLGen `pp_row_feedback` MAC into
  `npu/rtlgen/gen.py` as an optional GEMM backend and validate with RTL/perf
  compare plus block-level synthesis sweeps.
- Extend perf memory modeling fidelity (latency/burst/outstanding) and keep
  model assumptions synchronized with `npu/sim/perf/README.md`.
- Maintain finish-level fp16 backend sweep as a regression gate when changing
  fp16 datapath or numeric policy defaults.
