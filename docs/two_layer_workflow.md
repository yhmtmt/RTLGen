# RTLGen Two-Layer Optimization Workflow

## Purpose
Clarify the two optimization layers in RTLGen and define how they interact:
- Layer 1: parameterized circuit module exploration (C++ RTLGen).
- Layer 2: parameterized NPU architecture exploration (`npu/` flow).

This separation keeps module-level physical tuning and model-level architectural
search coupled but not conflated.

## Layer 1: Circuit Module Exploration (Physical-First)

### Scope
- Arithmetic/activation module generation from C++ RTLGen.
- Algorithmic variants and parameter sweeps (e.g., adder/multiplier/MAC style,
  widths, signedness, pipeline, backend choices).
- Module-level physical evaluation and PPA/runtimes.

### Primary objective
Find robust, physically competitive module implementations and parameter ranges
for each target PDK.

### Evaluation basis
- OpenROAD physical results (timing/area/power/runtime).
- Append-only module metrics under `runs/designs/<circuit_type>/<design>/`.

### Typical loop
1. Propose/implement circuit-generation algorithm candidates in C++ RTLGen.
2. Emit module RTL/configs and run physical sweeps.
3. Compare module PPA/runtime and record reproducible artifacts.
4. Freeze selected variants as reusable hardened macro artifacts where needed.

### Outputs consumed by Layer 2
- Module-level Pareto candidates and preferred parameter sets per PDK.
- Hardened macro artifacts (`macro_manifest.json`) and optional libraries
  (`macro_library.json`) for top-level hierarchical PnR.
- Supported parameter envelopes and known limits/failure modes.

## Layer 2: NPU Architecture Exploration (Model-First)

### Scope
- Architecture-level parameters and structural choices (`npu/arch`, `npu/rtlgen`).
- Novel architectural mechanisms (tiling, module composition, macro usage mode).
- Co-optimization of architecture parameters plus selected module parameters
  from Layer 1.

### Primary objective
For each target PDK, find the best NPU architecture under model-set objectives
using multiple real ONNX models.

### Evaluation basis
- Mapping + performance simulation on real ONNX workloads.
- Physical metrics integrated from OpenROAD runs.
- Campaign-level reporting/ranking (latency/throughput/energy + PPA/runtime).

### Typical loop
1. Define architecture search space and ONNX model set.
2. Select module candidates/hardened macros from Layer 1 outputs.
3. Run NPU physical + perf campaign (`npu/eval/*`).
4. Rank architecture points per PDK using campaign objectives/profiles.
5. Record best architecture recommendations and residual bottlenecks.

## Layer Interaction Contract

### Layer 1 -> Layer 2 (forward handoff)
- `macro_manifest.json` and/or `macro_library.json` for hierarchical runs.
- Module PPA/runtime tables with config hashes and parameter traceability.
- Recommended per-PDK module defaults and fallback options.
- Machine-readable candidate manifests:
  - `runs/candidates/<pdk>/module_candidates.json`
  - validated against referenced `runs/designs/.../metrics.csv` rows.

### Layer 2 -> Layer 1 (feedback handoff)
- Bottleneck-driven requests for new module algorithms or parameter regions.
- Per-PDK target envelopes (timing, area, power, runtime constraints).
- Prioritized sweep requests based on model-level objective sensitivity.

## Decision hierarchy
1. Layer 1 decides module implementation quality and feasible parameter ranges.
2. Layer 2 decides architecture composition and workload-level best points.
3. Final recommendation is per-PDK architecture point with explicit module
   selections and provenance to both layers.

## Canonical document map
- Role map: `docs/structure.md`
- Layer 1 runbook: `docs/layer1_circuit_workflow.md`
- Circuit/evaluation guidance: `notes/workflow.md`, `runs/README.md`
- Layer 2 runbook: `npu/docs/workflow.md`
- NPU campaign flow: `npu/eval/README.md`
