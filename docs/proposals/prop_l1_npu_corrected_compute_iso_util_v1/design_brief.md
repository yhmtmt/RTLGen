# Design Brief

- `proposal_id`: `prop_l1_npu_corrected_compute_iso_util_v1`
- scope: iso-utilization PPA separation for corrected FP16 NPU compute blocks
- baseline: corrected nm1 through nm64 frontier

The current frontier mixes architectural scaling and physical-utilization
pressure.  This proposal intentionally changes only the floorplan envelope while
keeping the same corrected RTL configurations.
