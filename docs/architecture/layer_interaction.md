# Layer Interaction Contract

## Purpose

Define the current practical interaction between:

- Layer 1 circuit exploration
- Layer 2 or Layer 3 architecture exploration

This is the operational handoff contract, not the generalized layer ontology.

## Layer 1 responsibility

Layer 1 decides:

- module implementation quality
- feasible parameter ranges
- per-PDK physical characteristics of reusable blocks

Typical outputs:

- module metrics in `runs/designs/.../metrics.csv`
- candidate manifests
- optional hardened macro manifests

## Higher-layer responsibility

Architecture/subsystem exploration decides:

- structural composition
- workload-visible behavior
- ranking across model or campaign objectives

Typical outputs:

- campaign summaries
- architecture recommendations
- bottleneck-driven requests back to lower layers

## Forward handoff

Lower layer to higher layer:

- candidate identity and config traceability
- evaluation scope:
  - `wrapped_io`
  - `macro_hardened`
- optional `macro_manifest.json`
- per-PDK preferred candidates and fallback options

## Feedback handoff

Higher layer to lower layer:

- bottleneck-driven requests for new circuit mechanisms
- tighter timing/area/power envelopes
- requests to harden a previously wrapped-only candidate
- mapper follow-on items when architecture questions are blocked by mapping

## Decision hierarchy

1. lower layer validates circuit feasibility and physical competitiveness
2. higher layer validates composition and workload-level value
3. final recommendations should cite both layers’ evidence
