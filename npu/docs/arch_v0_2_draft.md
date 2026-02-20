# NPU Architecture v0.2 Draft (Hierarchical)

## Purpose
Capture the architecture-layer decision for NPU exploration and define the
draft direction for `arch v0.2`.

## Current status
- **Implemented**: `npu/arch` v0.1 exists and can produce shell-centric RTLGen
  configs via `npu/arch/to_rtlgen.py`.
- **Implemented**: `arch v0.2-draft` schema and example are available:
  - `npu/arch/schema_v0_2_draft.yml`
  - `npu/arch/examples/minimal_v0_2_draft.yml`
- **Implemented**: `npu/arch/to_rtlgen.py` now supports `schema_version: 0.2-draft`
  and derives `compute.gemm`/`compute.vec` RTLGen candidates (including optional
  history-aware selection).
- **Gap**: validation is still shallow (required-key checks only), and
  interconnect/mapping fields are not yet consumed by mapper/simulator policy.

## Decision summary (from current discussion)
1) `npu/arch` should be the top-level architecture specification.
2) `npu/rtlgen` config should be a derived, detailed per-run configuration.
3) Derivation should use optimizer policy and run history.
4) The abstraction split is intentional to enable hierarchical and efficient
   parameter search.
5) To scale beyond lane-1 golden bring-up, architecture must include:
   - unit macro blocks (tile-level compute/memory blocks),
   - interconnection model (bandwidth/latency/topology),
   - hierarchical mapping constraints.

## Layering model
- Architecture intent layer (`npu/arch/*.yml`):
  - fixed interfaces and invariants
  - macro topology and constraints
  - search-space boundaries
- Derived implementation layer (`npu/rtlgen/*.json`):
  - concrete candidate values for one run
  - explicit backend and lane settings
  - hashable, immutable run input
- Search/history layer (`runs/...`):
  - candidate generation strategy
  - result feedback loop (PPA + correctness)

## Why this split matters
- Prevents overfitting architecture files to temporary generator internals.
- Enables coarse-to-fine search:
  - macro-level allocation first,
  - then micro-level implementation tuning.
- Makes multi-lane and multi-tile mapping feasible without flat combinational
  search blow-up.

## v0.2 draft scope
- Add explicit macro block declarations.
- Add explicit interconnect links/topology.
- Add mapping hierarchy and constraints.
- Add search intent and history hooks for candidate derivation.
- Preserve v0.1 compatibility while v0.2 is draft-only.

## Implemented milestones
1) Added `npu/arch/schema_v0_2_draft.yml` and draft examples.
2) Extended `npu/arch/to_rtlgen.py` to auto-select v0.2 schema by
   `schema_version` and derive v0.2-draft arch into RTLGen JSON.
3) Preserved v0.1 compatibility in the same adapter path.
4) Verified both v0.1 and v0.2 example flows through `npu/rtlgen/gen.py`.

## Related files
- `npu/arch/schema.yml` (current v0.1)
- `npu/arch/to_rtlgen.py` (v0.1 + v0.2-draft adapter)
- `npu/arch/schema_v0_2_draft.yml` (new draft)
- `npu/arch/examples/minimal_v0_2_draft.yml` (new draft example)

## Next steps
- Review and freeze `arch v0.2` required fields.
- Add validation tooling for v0.2 types/ranges/enums (beyond top-level key checks).
- Extend derivation to consume interconnect/mapping constraints for hierarchical
  mapper/simulator policy.
