# Design Brief

## Proposal
- `proposal_id`: `prop_l1_segmented_xy_mesh_noc_phase1_v1`
- `title`: `Materialize segmented deterministic-XY NoC Phase 1 router and cycle model`

## Problem
- The current architecture exploration uses segmented or scheduled NoC interpretations, but the concrete routed block was still a placeholder. Primitive anchors existed, yet there was no synthesizable router with explicit metadata, VC buffering, and RTL-backed cycle behavior.

## Phase-1 Scope
- Implement a five-port `N/E/S/W/local` router at 256-bit flit width.
- Use deterministic XY routing over endpoint IDs in a 4x4 mesh.
- Preserve explicit flit metadata: destination, source, tag, fragment, last, and VC.
- Provide four virtual channels with per-input/per-VC FIFOs and fair per-output round-robin arbitration.
- Use ready/valid backpressure.
- Add a 4x4 mesh composition and a cycle model checked against RTL on route/stall scenarios.
- Add a single-router wrapper/config for Nangate45 PPA.
- Drive every physical-wrapper ingress with full-width evolving state, cycle every destination/source/VC field, and vary sink backpressure so synthesis cannot erase inactive payload bits, VC FIFOs, or route branches. Treat source/sink state and counters as disclosed benchmark overhead.

## Out of Scope
- Aggregate 4x4 mesh physical placement.
- Workload-optimal mesh scheduling for full Llama7B traffic.
- Adaptive routing, QoS, or SRAM/HBM integration logic beyond the router/mesh transport fabric itself.

## Validation
- Generator smoke and explicit wrapper compile.
- Router RTL versus cycle-model trace under contention and backpressure.
- Mesh RTL versus cycle-model delivery order and latency on a routed end-to-end segmented transfer.
