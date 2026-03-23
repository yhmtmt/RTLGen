# RTLGen Abstraction Layering

## Purpose
Define the generalized abstraction stack for RTLGen and separate it from evaluation method and optimization workflow.

This document is the canonical source for what a "layer" means in the repository.

## Core Rule
A layer corresponds to a circuit or system abstraction level, not to a single evaluation method.

Physical evaluation may appear at multiple layers. Higher-layer modeling may use more abstract simulation, but those abstractions should be grounded in accepted evidence from lower layers.

## Generalized Layer Stack

### Layer 0: Device / Cell
Scope:
- standard cells
- custom cells
- SRAM/compiler interfaces
- characterization views

Typical evaluation:
- SPICE
- characterization
- layout-level physical verification

### Layer 1: Circuit Block
Scope:
- arithmetic units
- activations
- MACs
- buffers
- routers
- reusable parameterized modules from `src/rtlgen`

Typical evaluation:
- RTL generation
- logic synthesis
- OpenROAD physical sweeps
- module-level PPA/runtime comparison

### Layer 2: Architecture Block / Subsystem
Scope:
- tiles
- clusters
- fabrics
- subsystem-scale generators
- integrated proof targets that are larger than a single reusable block but smaller than a full product-scale system

Typical evaluation:
- subsystem physical evaluation
- synth-stage prefilters
- workload proxies
- reduced-top experiments

### Layer 3: Full Architecture / Accelerator
Scope:
- complete NPU / CPU / GPU / FPGA-style architecture generators
- top-level architecture composition and model-visible behavior

Typical evaluation:
- mapping and workload execution models
- performance simulation
- full-top physical evaluation
- architecture ranking on real workloads

### Layer 4: Multi-Die / Package / System
Scope:
- chiplets
- package-level composition
- memory/network/system integration

Typical evaluation:
- package/system models
- bandwidth/latency/thermal/power integration
- multi-die physical constraints

## Evaluation Modes Are Orthogonal
The following are evaluation modes, not layers:
- spice simulation
- RTL simulation
- synth prefilter
- physical sweep
- performance simulation
- measurement_only
- paired_comparison
- broad_ranking

A given layer can use multiple evaluation modes.

Examples:
- Layer 1 block work may use RTL simulation plus OpenROAD physical sweeps.
- Layer 3 architecture work may use performance simulation plus top-level physical evaluation.
- Lower-layer accepted physical evidence may be required before a higher-layer abstraction is trustworthy.

## Current Repository Mapping
The repository currently has two major active generator families:
- `src/rtlgen`: mostly Layer 1 circuit-block generation
- `npu/`: mostly Layer 3 architecture generation

The current operational "two-layer" wording in existing docs is therefore a practical current-state simplification:
- current `Layer 1` docs: block-level circuit generation and physical optimization
- current `Layer 2` docs: NPU architecture exploration and workload-level evaluation

That wording is acceptable as a description of today's active workflows, but it should not be treated as the final generalized ontology for the repository.

## Rule For Cross-Layer Claims
Higher-layer claims should identify their lower-layer evidence basis.

Examples:
- architecture perf claims may depend on accepted lower-layer physical parameters
- abstract performance simulation at a high layer should cite the lower-layer physical source used to parameterize it
- if a higher-layer feature introduces a new circuit mechanism, that mechanism may require lower-layer evidence before higher-layer evaluation is considered authoritative

## Relationship To Existing Workflow Docs
- `docs/two_layer_workflow.md` describes the current active two-family workflow
- `docs/layer1_circuit_workflow.md` describes current block-level physical optimization
- `npu/docs/workflow.md` describes the current NPU architecture workflow

When those docs say `Layer 1` / `Layer 2`, read them as current operational layers, not as a limit on future abstraction levels.
