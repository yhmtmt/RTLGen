# Design Brief

The counter-based generator directly drives the synthesized RX-before-TX
paired scheduler. Every generated command traverses finite endpoint descriptor
queues, one-cycle source-SRAM ports, bounded receive contexts, and the exact
segmented 4x4 mesh. The comparison covers packet/flit counts, drain cycles,
router contention, input stalls, and maximum occupancy.

The current packet-ID-derived base addresses are an identity-proof mechanism.
Compact per-endpoint payload allocation and lifetime reuse remain a follow-on
memory-controller closure item.
