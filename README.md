# RTLGen

RTLGen is a hardware-generation and optimization workspace with two coupled
layers:

1. `Layer 1`: parameterized circuit module generation + physical optimization.
2. `Layer 2`: parameterized NPU generation + architecture optimization on real
   ONNX workloads.

The repository is organized so each layer can iterate independently while
sharing reproducible artifacts and evaluation results.

## Layer 1: Circuit Module Generator + Physical Optimization

`Layer 1` focuses on circuit blocks generated from C++ RTLGen (adders,
multipliers, MACs, activations, MCM/CMVM, FP operators).

### Goal
- Improve module generation algorithms.
- Find best parameter settings per PDK using physical evaluation.

### Typical loop
1. Generate module RTL from JSON config.
2. Run OpenROAD sweeps for timing/area/power/runtime.
3. Compare candidates and keep append-only metrics in `runs/designs/`.

### Main entry points
- Generator config reference: `examples/about_config.md`
- Module generation: `rtlgen <config.json>` (or `build/rtlgen <config.json>`)
- Physical sweep scripts: `scripts/generate_design.py`, `scripts/run_sweep.py`
- Result storage: `runs/designs/<circuit_type>/<design>/metrics.csv`

## Layer 2: NPU Generator + Architecture Optimization

`Layer 2` focuses on NPU architecture exploration in `npu/`:
architecture config, RTL generation, mapping, physical synthesis integration,
and performance simulation.

### Goal
- Find best NPU architecture per PDK.
- Evaluate architecture and module choices on multiple actual ONNX models.

### Typical loop
1. Define architecture search points (`npu/arch/`).
2. Generate NPU RTL and optional hardened macro candidates.
3. Run mapping + physical + perf campaign (`npu/eval/`).
4. Rank points by objective profiles (latency/energy/PPA/runtime).

### Main entry points
- NPU docs hub: `npu/docs/index.md`
- NPU runbook: `npu/docs/workflow.md`
- Campaign tools: `npu/eval/run_campaign.py`, `npu/eval/report_campaign.py`,
  `npu/eval/optimize_campaign.py`
- Campaign artifacts: `runs/campaigns/npu/`

## Layer Interaction (Contract)

Layer coupling is explicit and file-based.

- `Layer 1 -> Layer 2`
  - Provides physically evaluated module candidates.
  - Candidate manifests declare whether results are `wrapped_io` or
    `macro_hardened` to prevent accidental macro assumptions.
  - Provides hardened macro artifacts (`macro_manifest.json`) and optional
    macro libraries.
- `Layer 2 -> Layer 1`
  - Sends bottleneck-driven requests for new module algorithms/parameter ranges
    based on model-level campaign outcomes.

Canonical specification for this split:
- `docs/two_layer_workflow.md`

## Quick Start

### Build
```sh
mkdir -p build
cd build
cmake ..
cmake --build .
```

### Layer 1 smoke run
```sh
build/rtlgen examples/config.json
```

### Layer 2 starting points
- `npu/setup.md`
- `npu/docs/workflow.md`

## Viewing Aggregated Evaluation Results

The static browser is at `docs/runs/index.html` and loads `runs/index.csv`.

```sh
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000/runs/index.html`.

If needed, regenerate the index:

```sh
python3 scripts/build_runs_index.py
```

## Documentation Map

- Repository documentation roles: `docs/structure.md`
- Layer 1 runbook (module physical optimization): `docs/layer1_circuit_workflow.md`
- Two-layer workflow and handoff contract: `docs/two_layer_workflow.md`
- Notes and studies: `notes/index.md`
- Planning log: `plan/log.md`
- NPU docs hub: `npu/docs/index.md`

## Environment

Devcontainer and toolchain details:
- `development.md`

Core dependencies include CMake/C++17, Google Test, OR-Tools, Yosys/GHDL,
and FloPoCo/PAGSuite integration.
