# Score32 Exact Shared Root To Global Tree Contract

This boundary connects the finite 15-source packet transport to the existing
16-leaf exact radix-2 reduction and finalization tree. It removes the aggregate
global-link abstraction without changing the proven local partial format.

## Leaf Identity

Remote sources 0 through 14 traverse the shared root endpoint, replay from
their independent packet SRAM banks, pass through one packet deframer per
source, and then pass through one exact stats-once decoder per source. Root
cluster 15 supplies the sixteenth canonical beat directly and does not consume
NoC bandwidth.

Each canonical beat is 419 bits and maps without arithmetic conversion:

- bits 15:0: command ID
- bits 20:16: head ID
- bits 52:21: signed global maximum
- bits 85:53: exponential sum
- bits 89:86: value slice
- bit 90: final slice
- bits 418:91: eight 41-bit partial value lanes

These fields drive the existing exact tree's packed leaf ports. Every leaf
retains its own ready/valid handshake. No FIFO, mux, or scheduler may consume a
leaf beat until the downstream tree path accepts that same beat.

## Context And Ordering

A group context is accepted atomically by the shared root endpoint and all 15
remote decoders. A source cannot begin transport from a context accepted by
only one side of the boundary. The root-local leaf must carry the same command,
head, slice, and last sequence as the 15 decoded leaves. Existing tree metadata
checks remain the authority for cross-leaf mismatch detection.

For every source, the decoder emits exactly 128 canonical beats in head-major,
slice-minor order. The global tree consumes corresponding beats from all 16
leaves and emits 128 exact finalized rows. Packet completion is not equivalent
to tree completion: packet slots may retire after decoder acceptance, while
leaf and tree backpressure continue independently downstream.

## Equivalence Gate

The composed RTL gate must prove:

- 15 x 128 transported beats and 128 root-local beats are accepted exactly
- all 16 leaf tuples match the canonical software/reference tuples bit-for-bit
- the exact tree emits all 128 expected finalized rows in order
- arbitrary independent leaf and root-output backpressure does not change data
- transport, decoder, tree, ordering, and finalizer protocol errors remain low
- synthesis retains one packet endpoint, 15 packet SRAM banks, 15 packet
  deframers, 15 exact decoders, and one 16-leaf radix-2 tree

The cycle report must separate root-link delivery, decoder drain, tree
completion, and finalizer completion. The measured 2,505-cycle root delivery
span is the transport floor; any additional composed latency is attributed to
decoder/tree/finalizer service or explicit downstream backpressure.
