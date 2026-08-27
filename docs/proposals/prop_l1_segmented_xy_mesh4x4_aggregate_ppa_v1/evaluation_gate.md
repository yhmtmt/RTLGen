# Evaluation Gate

- Dependency: merged promotion for `l1_segmented_xy_mesh_noc_phase1_v1_r7`.
- Execute only the r2 sweep with `FLOW_VARIANT=mesh4x4_aggregate_r2`; v1
  attempts reused an incomplete cached row and are not physical evidence.
- Required first result: one hierarchical 2 ns, 3.2 mm square feasibility row, or an explicit bounded synthesis/placement failure.
- A successful row is aggregate mesh-plus-boundary-harness evidence, not isolated mesh logic and not full attention-cluster PPA.
- A failed row defines the next hierarchy/runtime/area boundary; it must not be silently discarded.
