# Evaluation Gate

The synthesis diagnostic must retain both flat and hierarchy-preserving rows,
including elapsed time, peak memory, and exact failure phase. A resource limit
is a measured decomposition boundary, not circuit infeasibility.

Physical evaluation may start only after a viable synthesis path is selected.
Successful physical rows require finite timing, area, and power, timing-path
identity, exactly 120 SRAM macros, and nonzero area under every declared DUT
prefix. Failed floorplan, pin-placement, or routing rows remain explicit.
