# Layer 1 Workflow

## Purpose

Define the operational workflow for block-level circuit generation and physical
evaluation.

## Scope

- C++ RTL generator changes
- module config generation
- physical synthesis sweeps
- module candidate selection and handoff

## Standard loop

1. define candidate configs
2. generate RTL
3. run physical sweeps
4. compare append-only metrics
5. select candidates and hand off evidence upward

## Entry commands

Build:

```sh
mkdir -p build
cd build
cmake ..
cmake --build .
```

Generate RTL:

```sh
build/rtlgen <config.json>
```

Run sweeps:

```sh
python3 scripts/generate_design.py <config.json> <platform>
python3 scripts/run_sweep.py   --configs <config_or_list>   --platform <platform>   --sweep <sweep.json>   --out_root runs/<circuit_type>
```

Refresh aggregated index:

```sh
python3 scripts/build_runs_index.py
```

## Output contract

- lightweight committed evidence lives under `runs/designs/`
- `metrics.csv` remains append-only
- large temporary logs and work dirs stay out of committed artifacts

## Remote execution

Default path:

- DB-backed `l1_sweep` through the control plane

Fallback path:

- legacy/manual queue JSON only when DB-backed execution is unavailable

## Architecture-block policy

For early-stage integrated `architecture_block` items:

- preserve hierarchy first
- do not start with full flattening
- prefer legality or synth-prefilter, then reduced proxy physical runs, then
  selective later flattening if needed

## Related docs

- `docs/architecture/layer_interaction.md`
- `docs/workflows/evaluation_lanes.md`
- `npu/docs/workflow.md`
