# Score32 Exact Stats-Once Shared Root Contract

This boundary scales the proven one-source finite SRAM path to the complete
16-cluster reduction topology. Remote endpoints 0 through 14 send exact local
partials to root endpoint 15. The root cluster's own partial is the sixteenth
leaf and does not traverse the mesh.

## Traffic Identity

- one remote source group contains 128 canonical 419-bit beats
- stats-once encoding produces exactly 167 256-bit flits
- packet indices 0 through 19 contain eight flits; packet 20 contains seven
- tag is `{epoch[2:0], packet_index[4:0]}`
- `(source, VC, tag)` is the shared endpoint's live context key
- all 15 sources may therefore use the same epoch and packet index concurrently

The root ejection link accepts at most one flit per cycle. A complete remote
group set consequently has a hard serialization lower bound of 2,505 flits,
before route bubbles, SRAM stalls, decoder stalls, or global-tree backpressure.

## Shared Endpoint

Endpoint 15 is instantiated once, with at least 15 live RX contexts. It is not
replicated once per source. The root scheduler installs one context per source
before releasing that source's matching TX descriptor. Missing context is a
protocol error and is never used as flow control.

Descriptors are packet-major across sources. Each source may have at most one
packet context live. A completion retires that context and permits installation
of the source's next packet when its alternating destination slot is free.
The baseline static scheduler releases one complete 15-source packet round
every 120 cycles (`15 sources x 8 flits`). This matches the root ejection
capacity, produces a continuous root stream after fill, and remains valid for
the seven-flit terminal round. A dynamic scheduler may release earlier only if
it proves the same context and slot-reuse invariants.

The RTL latches a group barrier after all 15 remote contexts arrive and opens
packet index `n` at 120-cycle intervals. The complete real-mesh equivalence
trace delivers all 2,505 flits over exactly 2,505 cycles from first root
delivery through last root delivery. Thus the finite endpoint, SRAM replay,
and source scheduling add no root-ejection bubbles for this group.

## Destination Storage And Replay

Each remote source owns two eight-word 256-bit packet slots at the root. The
minimum root payload storage is therefore 15 independent 16x256 synchronous
SRAM banks, or 7,680 bytes. An accepted final write precedes registered packet
completion. Completion makes a slot replayable but does not make it free.

Each source independently replays completed packets in packet-index order into
one exact packet deframer and exact stats-once decoder. A slot becomes free only
after its final replay word is accepted. The 15 canonical leaf streams retain
independent ready/valid backpressure until the exact global tree consumes the
corresponding beat from every remote source; root-local leaf 15 joins there.

## Equivalence And Performance Gates

The RTL gate must prove:

- 15 x 128 canonical input beats equal 15 x 128 decoded output beats exactly
- 2,505 flits, 315 packets, descriptors, completions, and replays are conserved
- every source ID 0 through 14 reaches the single root endpoint
- contexts are installed before TX release and tags remain ordered per source
- no source exceeds two destination slots and no slot is reused before replay
- synthesis retains one shared endpoint and 15 packet SRAM instances

The performance model uses the actual registered-credit mesh and endpoint
descriptor timing. Its result is an optimistic NoC/control lower bound until
RTL replay and global-tree backpressure traces are compared cycle by cycle.
DRAM/HBM controller timing remains outside this contract.
