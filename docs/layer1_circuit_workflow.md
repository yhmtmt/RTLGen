# Layer 1 Circuit Workflow (Physical Optimization)

## Purpose
Define the operational workflow for Layer 1: parameterized circuit module
generation and physical optimization.

This runbook is the source of truth for module-level search loops. For NPU
architecture-level workflow, use `npu/docs/workflow.md`.

## Scope
- C++ RTLGen module generation (adder/multiplier/MAC/activation/MCM/CMVM/FP).
- Physical synthesis sweeps and PPA/runtime comparison.
- Candidate selection and handoff artifacts for Layer 2.

## Inputs
- Module config JSON (see `examples/about_config.md`).
- Target platform/PDK and sweep parameters.
- Optional baseline design IDs for A/B comparison.

## Outputs
- Per-design RTL + metrics under `runs/designs/<circuit_type>/<design>/`.
- Campaign summaries under `runs/campaigns/<circuit_type>/<campaign>/`.
- Optional hardened macro artifacts (when needed by Layer 2 hierarchical runs).

## Standard loop
1. Define candidate configs.
2. Generate RTL and sweep physical parameters.
3. Compare PPA/runtime and keep append-only metrics.
4. Select per-PDK candidate set and record rationale.
5. Handoff selected candidates to Layer 2 exploration.

## Execution steps

### 1) Build generator
```sh
mkdir -p build
cd build
cmake ..
cmake --build .
```

### 2) Generate a module RTL candidate
```sh
build/rtlgen examples/config.json
```

### 3) Run physical sweep
Use the flow wrappers that write into `runs/designs/`:
```sh
python3 scripts/generate_design.py <config.json> <platform>
python3 scripts/run_sweep.py \
  --configs <config_or_config_list> \
  --platform <platform> \
  --sweep <sweep.json> \
  --out_root runs/<circuit_type>
```

### 4) Aggregate and inspect
```sh
python3 scripts/build_runs_index.py
```
- Browser view: `docs/runs/index.html`
- Keep `metrics.csv` append-only; do not rewrite prior runs.

### 5) Select and hand off to Layer 2
- Record preferred per-PDK module variants and parameter ranges.
- For hierarchical NPU integration, provide:
  - design/config identity (`config_hash`, key parameters),
  - optional hardened macro views (`macro_manifest.json`) and selection rules.

## Data hygiene
- Keep committed artifacts lightweight (configs, RTL, `metrics.csv`, summaries).
- Do not commit large temporary logs or DEF/GDS.
- Preserve reproducibility with stable design names, tags, and parameter hashes.

## Related docs
- Two-layer split and interaction: `docs/two_layer_workflow.md`
- Artifact layout and contribution rules: `runs/README.md`
- Cross-project concepts/history: `notes/workflow.md`
- Layer 2 NPU workflow: `npu/docs/workflow.md`
