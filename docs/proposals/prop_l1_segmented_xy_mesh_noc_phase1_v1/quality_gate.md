# Quality Gate

## Proposal
- `proposal_id`: `prop_l1_segmented_xy_mesh_noc_phase1_v1`
- `title`: `Materialize segmented deterministic-XY NoC Phase 1 router and cycle model`

## Checks
- generator:
  - threshold: the single-router wrapper config generates under the existing `l1_memory_noc_primitive` flow without manual source edits.
- rtl_compile:
  - threshold: the generated wrapper elaborates with the copied helper RTL sources.
- router_equivalence:
  - threshold: the cycle model matches routed flit order and stall counters for a contention/backpressure scenario.
- mesh_equivalence:
  - threshold: the cycle model matches delivered flit order and latency for an end-to-end segmented transfer across the 4x4 mesh.

## Local Commands
- `pytest -q tests/test_noc_segmented_mesh.py`

## Result
- status: passed
- note: Aggregate mesh PPA and workload scheduling remain follow-on work.
