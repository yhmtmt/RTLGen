# Compact exact transport physical canary

This Layer 1 item measures the exact stats-once reduction-transport composition
that is now available in RTL: fifteen source encoders and packet adapters, the
real 4x4 mesh, the shared-root receive/storage path, the exact leaf adapter,
and the generated c16/r2/l8/b59 global tree. It does not embody the separate
112 shared-SRAM stream contexts or their packet traffic. The physical top has
35 input bits and 128 output bits. Its `composition` instance forces
`PHYSICAL_BANKS=15` and `USE_FAKERAM=1`.

The generated macro manifest declares exactly 120 `fakeram45_64x32` root
storage macros. Hierarchical area is measured only below
`composition/exact_transport_wrapper/`; the generated verification stimulus
is retained for activity and protocol coverage but is not claimed as DUT
area. `total_power_mw` is therefore a whole-harness upper bound, not a
workload energy result.

The canary deliberately uses a conservative 4 mm square envelope, one
placement density, and two clock points. It is a feasibility and accounting
anchor, not a final architecture ranking. The measured instance area will set
the follow-up utilization sweep without conflating a guessed floorplan limit
with the transport timing. HBM/DRAM remains external. This proposal does not
restore the retracted L2 Phase-2 schedule or any invalid finite-endpoint
frontier.
