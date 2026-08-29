# Evaluation Gate

- Dependency: merged promotion for `l1_segmented_xy_mesh_noc_phase1_v1_r7`.
- Execute r4 with `FLOW_VARIANT=mesh4x4_aggregate_r4_diag`; v1/r2 reused
  incomplete cache state and r3 reached `make` but did not transport the
  decisive ORFS stage log.
- Required first result: exactly one complete hierarchical 2 ns, 3.2 mm square
  feasibility row plus portable setup-path identity, or an explicit bounded
  synthesis/placement failure.
- A successful row is aggregate mesh-plus-boundary-harness evidence, not isolated mesh logic and not full attention-cluster PPA.
- A failed row defines the next hierarchy/runtime/area boundary; it must not be silently discarded.
- An r4 failure is admissible only with `make_returncode`, bounded ORFS log
  tails, and the retained result-directory inventory in its linked result.
- Keep r4 unassigned until the three-point hierarchy-matched bare-router result
  is recovered and reviewed; only then can the aggregate overhead be compared
  against a trustworthy primitive anchor.
