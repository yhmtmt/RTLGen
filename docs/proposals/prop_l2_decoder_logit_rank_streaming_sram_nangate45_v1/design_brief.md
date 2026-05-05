# Design Brief

Use the same decoder logit-rank streaming overlap model and measured rank/merge PPA as the memory/NoC run, but bind SRAM energy to the Nangate45 CACTI artifact committed for `minimal_v0_2_draft`.

The report should preserve the existing perf-sim/RTL equivalence contract:

- accepted `LogitTileStream` beat count
- accepted `CandidateStream` group count
- producer stall cycles
- candidate FIFO max occupancy
- final last-beat completion cycle
- deterministic candidate ordering and lower-token tie-break

NoC energy remains a first-order planning term until a measured NoC/router artifact exists.
