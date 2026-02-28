# NPU End-to-End Evaluation Flow Plan

## Purpose
Define and operationalize a single evaluation loop that connects:
- ONNX model mapping
- physical mapping (OpenROAD)
- performance simulation
- merged PPA/perf reporting

This plan is intentionally focused on flow completeness first, deep mapper
tuning second.

## Why this order
- Current per-stage experiments are useful, but difficult to compare at model
  level without a unified result contract.
- We need one reproducible campaign ledger before investing in large
  configuration search.

## Phase plan

### Phase 1: Contract lock (now)
Deliverables:
- campaign manifest contract
- merged result-row contract
- validator + examples
- first campaign skeleton for target ONNX models and architecture points

Definition of done:
- `python3 npu/eval/validate.py --campaign ...` passes
- `python3 npu/eval/validate.py --result-row ...` passes
- campaign file exists under `runs/campaigns/npu/`

### Phase 2: Orchestrator scaffolding
Deliverables:
- one runner command that executes:
  1) ONNX -> schedule/descriptor
  2) physical run selection + metric parsing
  3) perf sim run + trace parsing
  4) merged row append

Definition of done:
- one command produces append-only `results.csv` rows following contract.

### Phase 3: Physical-to-perf feedback loop
Deliverables:
- explicit use of physical timing (`critical_path_ns`) and power in model-level
  perf/energy metrics.

Definition of done:
- merged rows include latency/throughput/energy derived from physical metrics.

### Phase 4: Model-set reporting
Deliverables:
- campaign report with per-model and aggregate:
  - latency
  - throughput
  - energy
  - area/power/timing
  - physical runtime

Definition of done:
- report can rank architecture points for target model set.

### Phase 5: search/tuning loop
Deliverables:
- only after Phases 1-4 are stable, scale mapper/physical parameter sweeps.

Definition of done:
- best-point selection is based on model-level objective, not single-stage proxy.

## Current step started
Phase 1 has been started with:
- `npu/eval/` contract docs/schemas/validator
- `runs/campaigns/npu/e2e_eval_v0/campaign.json` skeleton
