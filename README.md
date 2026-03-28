# RTLGen

RTLGen is a hardware-generation and evaluation workspace spanning:

- circuit-block generation and physical evaluation
- accelerator generation, mapping, simulation, and campaign evaluation
- DB-backed remote evaluation orchestration

## Start here

- Documentation hub:
  - `docs/index.md`
- Repository structure:
  - `docs/repo/structure.md`
- Environment/bootstrap:
  - `docs/repo/environment.md`
- Layer model:
  - `docs/architecture/layers.md`
- Layer interaction:
  - `docs/architecture/layer_interaction.md`
- Layer 1 workflow:
  - `docs/workflows/layer1.md`
- Developer loop:
  - `docs/workflows/developer_loop.md`
- Internal vs external evaluation lanes:
  - `docs/workflows/evaluation_lanes.md`
- Control-plane operations:
  - `control_plane/operator_runbook.md`
- NPU subsystem workflow:
  - `npu/docs/workflow.md`

## Quick start

Build:

```sh
mkdir -p build
cd build
cmake ..
cmake --build .
```

Layer 1 smoke run:

```sh
build/rtlgen examples/config.json
```

View aggregated results:

```sh
python3 -m http.server 8000 --directory docs
```

Then open `http://localhost:8000/runs/index.html`.
