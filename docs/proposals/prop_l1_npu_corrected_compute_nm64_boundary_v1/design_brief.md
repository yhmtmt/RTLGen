# Design Brief

- `proposal_id`: `prop_l1_npu_corrected_compute_nm64_boundary_v1`
- scope: corrected FP16 NPU compute nm64 physical boundary
- baseline: corrected nm1 through nm32 frontier merged in PR #669

The corrected nm32 flat point measured `6.3103 ns`, `1.95 mW`, and about
`731536 um^2` stdcell area in a `2250000 um^2` die area.  That leaves enough
area headroom to test nm64 before assuming that scheduler hierarchy or NoC work
is the immediate bottleneck.
