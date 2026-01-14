# RTLGen NPU Development & Evaluation Flow (NVDLA-based) — Requirements

This document lists requirements to extend **RTLGen** (current generate→synthesize→evaluate loop for adders/multipliers) into an **NPU architecture + datapath co-design** workflow, reusing the **NVDLA “shell”** concepts (host interface, DMA, command queue, interrupts) while targeting **modern multimodal/transformer-style workloads**.

Current repo status to anchor scope:
- RTLGen generates and evaluates small arithmetic blocks via `scripts/generate_design.py` and `scripts/run_sweep.py`.
- Results are stored under `runs/designs/**/metrics.csv` and indexed by `runs/index.csv` (see `doc/workflow.md`).
- Evaluation guidance lives in `doc/evaluation_agent_guidance.md`; development/branching policy in `doc/development_agent_guidance.md`.
- There is no NPU-specific RTL, mapper, or simulator yet; those are future deliverables.

---

## 1. Goals and non-goals

### Goals
- Provide a **closed-loop** workflow:
  1) generate/modify NPU RTL (architecture + datapath variants)  
  2) run **physical synthesis** (OpenROAD) for key blocks or whole NPU (as feasible)  
  3) estimate **PPA + bandwidth/latency constraints**  
  4) acquire benchmark models and workloads  
  5) **map / schedule** onto target NPU  
  6) run **abstracted simulation** (GPU computes; NPU constraints determine timing/throughput)  
  7) score and iterate (auto-tuning / search / ablation)
- Keep the workflow **reproducible**, **parameterized**, and **extensible** to new NPU designs and workloads.

### Non-goals (initially)
- Full cycle-accurate RTL simulation of the complete NPU.
- Implementing a full production compiler stack from scratch (reuse TVM/MLIR where possible).
- Perfect power modeling at first iteration (start with proxies; refine later).

---

## 2. System-level architecture baseline (NVDLA-style shell)

### Required baseline features to reuse/adapt
- **Host-visible control plane**
  - MMIO register interface (or equivalent)
  - command submission via **ring buffer / command queue**
  - **events/fences** and **interrupts**
  - multi-context support (optional in v1, but API must not block it)
- **Memory interface**
  - AXI-like DMA model: bulk tensor copies + strided 2D copies
  - support for **gather/scatter** or indexed reads for KV/paged layouts
  - optional: IOMMU/ATS hooks (kept abstract)
- **Debuggability**
  - trace markers, perf counters, error reporting, deterministic replay hooks

### Deliverables
- A **stable “shell contract”** spec (host↔NPU) in Markdown:
  - command buffer format
  - descriptor formats (tensor, KV page, events)
  - error codes and debugging hooks

---

## 3. NPU microarchitecture modeling requirements

### Architecture parameterization
The NPU generator must accept a declarative configuration (YAML/JSON/TOML), including at least:
- Tensor core array shape and datatype modes (FP16/BF16/INT8/FP8…)
- On-chip SRAM sizes and banking (activation SPM, weights, KV SRAM)
- NoC/crossbar topology assumptions (at least abstract bandwidth & arbitration)
- DMA engine counts, peak BW, outstanding transactions
- KV-cache subsystem parameters:
  - paged KV format (page size, layout, per-head banking policy)
  - prefetch depth, writeback strategy, eviction policy (even if “software-managed”)
- Supported ops / ISA subset (GEMM, elementwise, softmax, norm, pack/unpack, etc.)

### Instruction/control model
Even if the RTL is not fully instruction-driven initially, the evaluation flow must define:
- a minimal **core instruction set / command primitives**:
  - TILE_LOAD / TILE_STORE
  - GEMM
  - vector ops (RMSNorm/LayerNorm, activation, reductions)
  - softmax
  - gather/scatter or KV-page read/write primitives
  - event wait/signal
- dependency model (events/fences) and concurrency rules

### Deliverables
- `arch/schema.yml`: canonical architecture schema
- `arch/examples/*.yml`: example configs (NVDLA-2-like, minimalist, high-BW, etc.)
- `isa/spec.md`: instruction/command semantics and constraints

---

## 4. RTL generation requirements (RTLGen integration)

### Generator behavior
- Generate RTL for:
  - compute tiles/arrays (parametric)
  - local SRAM wrappers / banking
  - DMA engines (at least placeholders + bus protocol stubs)
  - shell/control plane modules (queue, regs, IRQ)
- Support **incremental replacement**:
  - keep NVDLA-like shell stable while swapping compute core(s)
- Produce **standard outputs**:
  - synthesizable Verilog/SystemVerilog
  - metadata (module list, clocks/resets, top-level IO)
  - constraints template (SDC) and floorplan hints (optional)

### Current RTLGen baseline
- Config-driven RTL generation exists for adders/multipliers (JSON configs in `runs/campaigns/**/configs/`).
- `scripts/generate_design.py` emits `runs/designs/<circuit_type>/<design>/verilog/` and `config.json`.
- Generated designs are meant to be immutable inputs to evaluation; new experiments should create new design directories (per `doc/evaluation_agent_guidance.md`).

### Versioning
- Every generated design must have a **content-addressed ID**:
  - config hash (arch + RTLGen code version + pdk + tool versions)
  - stored alongside results for reproducibility

---

## 5. Physical synthesis / PPA estimation (OpenROAD)

### Tooling integration
- OpenROAD scripts must run **headless** and be reproducible:
  - pinned PDK(s): e.g., Sky130HD / Nangate45 / others as supported
  - standardized ORFS flow invocation
- Support two tiers:
  1) **Block-level** PPA for key macros (tensor core tile, SRAM wrapper, DMA)
  2) **SoC-level** (optional) for top-level timing closure approximations

### Current evaluation flow
- `scripts/run_sweep.py` drives ORFS and appends rows to `metrics.csv`.
- `scripts/build_runs_index.py` rebuilds `runs/index.csv` from all `metrics.csv` files.
- ASAP7 report units require conversion (critical path ps→ns, total power uW→mW).

### Required outputs
- Timing: Fmax, worst slack, path stats
- Area: cell area, macro area, utilization
- Power: at least proxy (switching estimation) and/or normalized model
- Artifacts: reports, DEF/GDS (if produced), logs, version stamps

### Cost controls
- Cache reuse: avoid resynthesizing identical blocks/configs
- Parallelization support (local or cluster execution hooks)

---

## 6. Workload acquisition and benchmark management

### Model sources
- Fetch benchmark models from the internet (with reproducible pins):
  - Hugging Face (Transformers), ONNX Model Zoo, timm, etc.
- Must support:
  - model + tokenizer + preprocessing versions
  - input sets (prompt corpora / image sets) with hashes
  - license tracking (store license metadata)

### Required benchmark suite types
- Transformer decoder (LLM decode), prefill vs decode split
- Vision encoder (ViT/ConvNext) and multimodal fusion blocks
- Audio encoder (optional)
- End-to-end multimodal pipelines (at least 1–2 reference models)

### Deliverables (future)
- `bench/manifest.yml`: reproducible benchmark definitions
- `bench/fetch.py`: downloader with hash verification
- `bench/licenses/`: license summaries and source references

---

## 7. Mapping / scheduling requirements

### Compiler integration
- Prefer reuse of existing stacks:
  - TVM, MLIR (IREE), ONNX Runtime, or custom lightweight mapper
- Must output an **intermediate schedule plan** that includes:
  - op tiling parameters
  - memory placement decisions (SPM/KV SRAM/DRAM)
  - DMA transfer plan (what/when)
  - concurrency plan (overlap DMA/compute)
  - quantization/casting plan (if used)

### Architectural legality checks
- Validate:
  - SRAM capacity and banking conflicts
  - DMA bandwidth and outstanding limits
  - tensor core utilization constraints
  - KV page residency constraints
  - alignment/layout constraints

### Deliverables (future)
- `mapper/ir.md`: schedule IR specification
- `mapper/run.py`: map a benchmark to a config, producing schedule IR + stats

---

## 8. Abstracted simulation requirements (GPU compute, NPU-timed)

### Core principle
- Numerical results are computed on **GPU/CPU** using reference kernels.
- Performance is measured by enforcing **NPU constraints**:
  - compute throughput limits (TOPS/TFLOPS, array shape)
  - memory bandwidth/latency limits (DMA, SRAM, KV)
  - scheduling dependencies/events
  - quantization/coarser computation if allowed (approx modes)

### Simulator capabilities
- Two modes:
  1) **Analytical** (fast): per-op cost models + bandwidth model
  2) **Trace-driven** (accurate-ish): event timeline simulation with resource contention
- Must produce:
  - end-to-end latency and throughput (prefill, decode tokens/s)
  - per-op breakdown (time, stalls, transfers)
  - resource utilization (tensor core, DMA, SRAM banks, KV)
  - “roofline-ish” diagnostics (compute vs BW bound)

### Fidelity controls
- Configurable modeling knobs (latency tables, BW curves, contention models)
- Calibration hooks using real PPA/frequency from OpenROAD results

### Deliverables (future)
- `sim/model.py`: cost model APIs
- `sim/run.py`: run schedule IR + arch config → timeline + metrics
- `sim/report.md`: standardized report template

---

## 9. Metrics, scoring, and optimization loop

### Metrics
- Performance:
  - latency, throughput, tail latency (p95/p99 if batching)
  - tokens/s for decode, images/s for vision
- Efficiency proxies:
  - energy proxy = (op_count * energy/op) + (bytes_moved * energy/byte)
  - area-normalized performance
- Feasibility:
  - timing closure margin, SRAM usage margin, BW headroom

### Scoring
- A single composite score should be optional; always keep raw metrics.
- Support **Pareto frontier** tracking (PPA vs perf).

### Search loop requirements
- Must support:
  - manual sweeps
  - Bayesian optimization / evolutionary search (optional)
  - constraint-driven pruning (early reject invalid configs)
- Store every trial with:
  - config hash
  - tool versions
  - synthesis + sim outputs
  - benchmark versions

---

## 10. Data formats, result management, and reproducibility

### Canonical artifacts per run
- `runs/designs/<circuit_type>/<design>/config.json` (immutable copy)
- `runs/designs/<circuit_type>/<design>/verilog/` generated sources
- `runs/designs/<circuit_type>/<design>/metrics.csv` evaluation results
- `runs/index.csv` aggregate index (generated)
- Future NPU additions should follow the same append-only data model.

### Determinism
- Pin:
  - PDK versions
  - OpenROAD/ORFS versions
  - compiler versions
  - benchmark versions and hashes
- Provide a `repro.sh` or `make repro` that recreates a run from its ID.

---

## 11. CI, automation, and developer ergonomics

### Continuous integration
- Smoke tests:
  - generate RTL for 1–2 configs
  - synthesize a small block (tensor tile) on a lightweight PDK
  - run mapping + simulator on a tiny benchmark
- Regression checks:
  - schema compatibility
  - report parsing
  - performance model sanity (no NaNs, monotonicity checks)

### Dev UX
- Single entrypoint CLI:
  - `rtlgen npu gen ...`
  - `rtlgen npu synth ...`
  - `rtlgen npu bench fetch ...`
  - `rtlgen npu map ...`
  - `rtlgen npu sim ...`
  - `rtlgen npu sweep ...`
- Good logs + structured JSON outputs for tooling.

### Current guidance
- Use feature branches for algorithm changes and keep legacy behavior behind config switches.
- Record evaluation scope and parameter ranges in docs before merging.

---

## 12. Security and licensing (pragmatic minimum)

- Track licenses for:
  - imported benchmark models
  - borrowed RTL/IP blocks
  - compiler components
- Ensure benchmark download scripts preserve attribution metadata.

---

## 13. Suggested repo layout (optional but recommended)

```
rtlgen/
  scripts/      # generators, sweeps, index building
  runs/         # designs, campaigns, metrics, index
  doc/          # workflow + evaluation/development guidance
  npu/          # (future) NPU-specific generators, specs, and flows
    arch/       # schema + example configs
    shell/      # NVDLA-like host/memory shell RTL and specs
    core/       # compute core(s): gemm, vector, pack/unpack
    kv/         # KV cache manager RTL + model
    rtlgen/     # generators and templates
    synth/      # OpenROAD flow scripts + parsing
    bench/      # manifests, downloaders, datasets
    mapper/     # mapping/scheduling, IR
    sim/        # abstracted simulation engine
    results/    # cached runs by hash
    docs/       # design notes, ISA spec, methodology
```

---

## 14. Acceptance criteria (v1)

A v1 is “usable” when:
- You can generate an NVDLA-2-like shell + a GEMM core RTL variant.
- OpenROAD can synthesize at least the GEMM tile and report Fmax/area.
- A benchmark (e.g., a small decoder-only model) can be fetched reproducibly.
- Mapping emits a schedule IR that passes legality checks.
- Abstracted simulation outputs:
  - prefill latency
  - decode tokens/s
  - breakdown showing BW stalls vs compute
- The full pipeline is runnable via a single CLI command, and results are cached by hash.

---

## 15. Open questions to track (not blockers)

- How much ISA vs fixed-function to adopt for the first tapeout-grade target?
- KV cache: how much is hardware-managed vs software-managed?
- Power modeling: which proxies best correlate with post-layout estimates?
- Multi-model / multimodal scheduling (vision+text fusion) and memory contention.
