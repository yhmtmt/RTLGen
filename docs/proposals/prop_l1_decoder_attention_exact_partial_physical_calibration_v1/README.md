# Exact-partial physical calibration

This package prepares two remote Nangate45 evaluation items and intentionally
does not dispatch either item.

The temporal/finalizer item measures one real temporal clock island with 104
`fakeram45_64x32` state macros. Divider-lane variants are separate designs.
The 1600 um die and 1500 um core are conservative relative to the calculated
129,024.896 um2 raw macro area.

The temporal pair merge must use `mersenne24_correction2_exact` for division by
`2^24-1`. This is bit-exact with the generic constant divider and avoids the
generic Yosys `TECHMAP` expansion. The calibration guard rejects generic
`/ 16777215` operators in this path.

The async-FIFO item contains source-domain and destination-domain variants.
Each variant uses the external `clk` only for the selected timing domain and a
protocol-safe generated helper clock for the inactive side. These are
per-domain diagnostics, not a common-clock or CDC-signoff measurement.

At queue time, use merged `origin/master` as the task source commit. The normal
L1 task generation request must place that SHA in
`source_requirement.required_sha`.
