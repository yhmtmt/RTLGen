# RTLGen

RTLGen is a hardware-generation and optimization workspace with two currently active operational layers:

1. `Layer 1`: parameterized circuit module generation + physical optimization.
2. `Layer 2`: parameterized NPU generation + architecture optimization on real
   ONNX workloads.

The repository is organized so each active layer can iterate independently while
sharing reproducible artifacts and evaluation results.

Generalized layer meaning is defined by abstraction level, not by one fixed
evaluation method. The current two-layer model is the repository's present
active instantiation, not the final ontology.

Canonical generalized layer spec:
- `docs/abstraction_layering.md`

## Evaluator First Read

If you are executing a queued evaluation task on a high-performance machine,
read these first:

1. `notes/evaluation_agent_guidance.md`
2. `runs/eval_queue/README.md`
3. The assigned item under `runs/eval_queue/openroad/queued/`

If you are operating the internal cross-host evaluation system instead of the
manual queue/PR lane, start here instead:

1. `control_plane/operator_runbook.md`
2. `control_plane/daily_operations.md`
3. `docs/internal_external_evaluator_policy.md`
4. `docs/developer_agent_first_read.md`
5. `docs/developer_agent_loop.md`

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
4. For remote heavy execution:
   - internal/trusted lane: use the DB-backed control plane in `control_plane/`
   - external/manual lane: queue tasks in `runs/eval_queue/openroad/`

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
- `docs/abstraction_layering.md`
- `docs/two_layer_workflow.md`
- `docs/internal_external_evaluator_policy.md`

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

- Evaluator first-read manual: `notes/evaluation_agent_guidance.md`
- Evaluation queue workflow/rules: `runs/eval_queue/README.md`
- Control-plane operator runbook: `control_plane/operator_runbook.md`
- Control-plane daily operations: `control_plane/daily_operations.md`
- Internal vs external evaluation policy: `docs/internal_external_evaluator_policy.md`
- Developer-agent first read: `docs/developer_agent_first_read.md`
- Development intake backlog: `docs/development_items/README.md`
- Notebook-side developer-agent loop: `docs/developer_agent_loop.md`
- Repository documentation roles: `docs/structure.md`
- Layer 1 runbook (module physical optimization): `docs/layer1_circuit_workflow.md`
- Two-layer workflow and handoff contract: `docs/two_layer_workflow.md`
- Notes and studies: `notes/index.md`
- Planning log: `plan/log.md`
- NPU docs hub: `npu/docs/index.md`

## Environment

Devcontainer and toolchain details:
- `docs/development.md`

Core dependencies include CMake/C++17, Google Test, OR-Tools, Yosys/GHDL,
and FloPoCo/PAGSuite integration.
