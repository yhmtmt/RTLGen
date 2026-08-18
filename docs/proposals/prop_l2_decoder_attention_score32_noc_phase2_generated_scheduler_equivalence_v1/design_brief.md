# Design Brief

The counter-based generator directly drives the synthesized RX-before-TX
paired scheduler. Every generated command traverses finite endpoint descriptor
queues, one-cycle source-SRAM ports, bounded receive contexts, and the exact
segmented 4x4 mesh. The comparison covers packet/flit counts, drain cycles,
router contention, input stalls, and maximum occupancy.

Generated commands use bounded endpoint-local addresses: shared slots 0..67,
reduction-source slots 68..100, and source-indexed root reduction receive
slots 68..562. The performance model certifies descriptor-to-final-memory-
operation lifetimes, while the RTL scoreboard maintains independent per-
endpoint live-slot bitmaps and rejects premature reuse. Producer fill and
consumer drain handshakes remain a follow-on composition item; SRAM bitcells
and macro placement remain physical evidence.
