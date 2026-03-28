# RTLGen Abstraction Layers

## Purpose

Define what a layer means in this repository.

A layer is an abstraction level, not an evaluation method.

## Layer stack

### Layer 0: Device / Cell

Scope:

- standard cells
- custom cells
- SRAM/compiler interfaces
- characterization views

### Layer 1: Circuit Block

Scope:

- arithmetic units
- activations
- MACs
- reusable parameterized modules from `src/rtlgen`

### Layer 2: Architecture Block / Subsystem

Scope:

- tiles
- clusters
- reduced-top subsystem proofs
- integrated blocks smaller than a full architecture

### Layer 3: Full Architecture

Scope:

- complete accelerator generators
- top-level architecture behavior and workload-visible effects

### Layer 4: Package / System

Scope:

- chiplets
- package composition
- system-level integration

## Evaluation modes are orthogonal

Examples of evaluation modes:

- RTL simulation
- synth prefilter
- physical sweep
- performance simulation
- measurement-only
- paired comparison

Any layer may use multiple evaluation modes.

## Current active repository mapping

The currently active generator families are:

- `src/rtlgen`
  - mostly Layer 1 circuit-block work
- `npu/`
  - mostly Layer 3 architecture work

Operational docs still use Layer 1 / Layer 2 as a practical shorthand for
the current active workflow split. That shorthand does not replace the full
abstraction model above.

## Cross-layer rule

Higher-layer claims must identify their lower-layer evidence basis when they
depend on lower-layer physical assumptions.
