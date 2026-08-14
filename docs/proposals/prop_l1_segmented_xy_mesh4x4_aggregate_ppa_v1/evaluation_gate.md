# Evaluation Gate

- Dependency: merged promotion for `l1_segmented_xy_mesh_noc_phase1_v1` generated from the corrected full-width harness.
- Required first result: one hierarchical 2 ns, 3.2 mm square feasibility row, or an explicit bounded synthesis/placement failure.
- A successful row is aggregate mesh-plus-boundary-harness evidence, not isolated mesh logic and not full attention-cluster PPA.
- A failed row defines the next hierarchy/runtime/area boundary; it must not be silently discarded.
