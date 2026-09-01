# Exact Dual-Producer Shared-Mesh Physical Calibration

This Layer 1 proposal measures the hierarchy already proven by the full
70,948-flit simultaneous RTL replay. It replaces separately costed VC0 and VC1
networks with one embodied mesh and sixteen endpoint VC arbiters.

The first evaluator item is deliberately synthesis-only. Its result chooses
between monolithic hierarchy-preserving synthesis and a composition of
separately hardened RTL macros before OpenROAD placement is attempted.

HBM/DRAM remains outside the RTL boundary. Arithmetic precision is unchanged.

`replacement_contract.json` fixes the downstream area ownership before the
measurement is available. It proves that the current ranked score32 area omits
the old primitive NoC overhead, retains compute/controller/KV/local SRAM and
reserve, and leaves 143.303824 mm2 for the measured reusable hierarchy.

`service_envelope.json` records a separate no-artificial-stall RTL pass. The
full exact traffic drains in 15,769 cycles, setting a 26.730382 ns standalone
capacity threshold against the current compute layer. It is not used as a
throughput result until actual producer release timing is replayed.
