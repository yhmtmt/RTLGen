# Exact Dual-Producer Shared-Mesh Physical Calibration

This Layer 1 proposal measures the hierarchy already proven by the full
70,948-flit simultaneous RTL replay. It replaces separately costed VC0 and VC1
networks with one embodied mesh and sixteen endpoint VC arbiters.

The first evaluator item is deliberately synthesis-only. Its result chooses
between monolithic hierarchy-preserving synthesis and a composition of
separately hardened RTL macros before OpenROAD placement is attempted.

HBM/DRAM remains outside the RTL boundary. Arithmetic precision is unchanged.
