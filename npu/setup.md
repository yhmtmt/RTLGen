# NPU Environment Setup Plan

## Purpose
This document defines a sequential workflow to establish the NPU development and evaluation toolchain inside the RTLGen repository.

## Current status (as of 2026-02-20)
- RTL shell bring-up and AXI memory simulation are implemented.
- AXI-Lite MMIO wrapper is available for the generated top.
- Mapper can emit binary descriptors for the RTL sim path.
- SRAM address map + AXI router integrated in RTL sim.
- CACTI PPA flow integrated for SRAM estimation (>90nm scaling).
- OpenROAD block flow wrappers are implemented under `npu/synth/`.
- fp16 backend sweep was completed at `make_target=finish`
  (`runs/designs/npu_blocks/fp16_backend_decision_nangate45.md`).

## Phase 0: Repository scaffolding
- Create `npu/` subtree for NPU-specific assets.
- Add a top-level `npu/README.md` describing the directory purpose and ownership.
- Keep all NPU toolchain scripts and configs under `npu/` to avoid mixing with existing `runs/` workflows.

## Phase 0.5: Devcontainer/toolchain prerequisites
- Base build tools: `build-essential`, `cmake`, `ninja-build`, `git`, `python3`, `python3-venv`.
- VP dependencies (from NVDLA VP README): `g++`, `libboost-dev`, `libglib2.0-dev`, `libpixman-1-dev`,
  `liblua5.2-dev`, `swig`, `libcap-dev`, `libattr1-dev`.
- SystemC 2.3.0 build/install (for VP):
  - Download SystemC 2.3.0a source.
  - Configure with `--prefix=/usr/local/systemc-2.3.0`.
  - Build and install; export `SYSTEMC_PREFIX=/usr/local/systemc-2.3.0`.
- TVM (scheduler) setup:
  - Prefer source build with a pinned commit; record the hash in setup notes.
  - Capture Python package requirements in `npu/mapper/requirements.txt`.
  - Keep TVM runtime optional in devcontainer; only required for mapper runs.

### Devcontainer verification checklist
- `python3 --version` and `cmake --version` succeed.
- Boost headers resolved: `ls /usr/include/boost` works (or PPA-installed path).
- SystemC installed:
  - `/usr/local/systemc-2.3.0/include` exists
  - `/usr/local/systemc-2.3.0/lib` contains `libsystemc`
- OpenROAD binary resolves: `openroad -version`.
- ORFS autotuner env exists: `ls /orfs/tools/AutoTuner/autotuner_env`.

## Phase 1: NVDLA integration baseline
- Import NVDLA reference repositories as submodules under `npu/nvdla/`:
  - `npu/nvdla/hw` (RTL, cmod, syn scripts, spec)
  - `npu/nvdla/sw` (KMD/UMD, runtime)
  - `npu/nvdla/vp` (SystemC virtual platform)
  - `npu/nvdla/doc` (Sphinx docs)
- Record source URLs, commit hashes, and licenses in `npu/nvdla/README.md`.
- Capture external documentation links for hardware, software, and VP.
- Define a "shell contract" file in `npu/shell/spec.md` that documents the host interface, DMA model, and command queue format.

## Phase 2: Architecture parameterization
- Define a canonical architecture schema in `npu/arch/schema.yml`.
- Add example configurations in `npu/arch/examples/`.
- Provide a validation script (Python) in `npu/arch/validate.py` to enforce schema requirements.
- Note: NVDLA `nvdlav1` hardware is fixed at 2048 8-bit MACs; initial parameterization
  should focus on RTLGen-generated wrappers/tiles while keeping the NVDLA shell stable.

## Phase 3: RTLGen integration
- Implement a generator entrypoint under `npu/rtlgen/` that can emit NPU modules based on the schema.
- Keep NVDLA shell stable while allowing compute core swapping.
- Emit outputs similar to existing RTLGen flows:
  - `verilog/` sources
  - `config.json` or `arch.yml` snapshot
  - metadata describing clocks/resets/IO

## Phase 4: OpenROAD evaluation flow
- Add OpenROAD wrappers under `npu/synth/` for block-level PPA runs.
- Use NVDLA `hw/syn` scripts as reference inputs for constraints and targets.
- Define macro-level floorplanning guidance for NPU tiles in `npu/synth/floorplan.md`.
- Ensure the flow runs inside the devcontainer environment and records results compatible with `runs/` indexing.

## Phase 5: Mapping and scheduling
- Integrate a scheduler backend (TVM or equivalent) under `npu/mapper/`.
- Define a schedule IR in `npu/mapper/ir.md`.
- Add a driver script `npu/mapper/run.py` to map a benchmark to an arch config and emit schedule stats.
- Track NVDLA SW runtime interfaces for loadable submission and queue semantics.
- Capture build requirements for the NVDLA KMD/UMD and test applications as part of
  the environment setup notes.

## Phase 6: Simulation environment
- Implement a simulator under `npu/sim/` that consumes schedule IR + arch config.
- Support analytical mode first; trace-driven simulation as a follow-up.
- Define output metrics formats in `npu/sim/report.md`.
- NVDLA VP requires SystemC 2.3.0 and additional build dependencies; capture
  these requirements in setup documentation for the devcontainer.
- VP runs require a platform config (e.g., `conf/aarch64_nvdla.lua`) and a Linux
  kernel image; document how to build or obtain these artifacts.
- VP/SystemC is intended for logical validation and integration checks only; it is
  too slow for practical LLM-scale evaluation. Plan a GPU-assisted simulator
  (standalone or coupled to VP) for performance studies.

## Phase 7: End-to-end workflow glue
- Add a single sequential pipeline script (or Makefile) in `npu/` that runs:
  1) arch validation
  2) RTL generation
  3) OpenROAD block synthesis
  4) mapping
  5) simulation
  6) report aggregation
- Ensure all outputs are recorded with stable IDs and hashes.

## Initial deliverables checklist
- `npu/README.md`
- `npu/setup.md` (this file)
- `npu/nvdla/README.md` documenting source and license
- `npu/arch/schema.yml` + one example config
- `npu/shell/spec.md`
- `npu/synth/floorplan.md`
- `npu/mapper/ir.md`
- `npu/sim/report.md`

## Next steps
- Keep setup dependencies synchronized with CI workflow requirements.
- Add TVM/mapper requirements once the mapper is wired to real models.
- Add compute-enabled OpenROAD runbooks beyond fp16 backend comparison.
