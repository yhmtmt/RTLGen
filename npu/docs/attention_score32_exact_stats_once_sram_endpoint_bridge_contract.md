# Score32 Exact Stats-Once SRAM Endpoint Bridge Contract

This follow-on composes the stats-once codec packet stream with
`noc_sram_packet_endpoint`. It replaces direct mesh injection with finite
packet storage, descriptor queues, SRAM request/response timing, receive
contexts, and completion-driven reclamation.

## Source Side

The source bridge owns at least two packet slots of eight 256-bit words each.
It fills one slot from the codec while the endpoint drains another. A TX
descriptor becomes visible only after every payload word for that packet has
been written. Its base address is the slot base, and its flit count is eight or
seven for the terminal packet.

The endpoint may issue several reads before their responses return. The memory
adapter captures the addressed payload at each accepted read request and holds
responses in order. A source slot is reusable only after all of its read
requests have been accepted and their payload values have entered that response
storage. Descriptor acceptance alone is not a release event.

## Destination Side

The root scheduler reserves a receive slot and installs the exact
`(source, VC, tag, base, count)` context before releasing the matching TX
descriptor. The endpoint writes each accepted fragment directly into the slot.
The slot becomes readable only after the registered packet completion is
accepted, which proves the terminal SRAM write was accepted.

Completed packets are retired to the decoder in packet-index order for each
source and group epoch. A slot is reusable only after its final word is accepted
by the stats-once decoder. If no receive slot is available, the scheduler must
withhold the TX release; sending a packet without a live receive context is a
protocol error, not a legal backpressure mechanism.

## Ordering and Capacity

- one group contains 21 packets and 167 flits
- packet slots are parameterized; two is the minimum ping-pong implementation
- descriptors and completions carry the packet tag from the packet bridge
- one group per source/epoch may be live
- different sources may interleave at the root, but packets from one source
  remain ordered
- one decoder is retained per remote source in the 16-cluster architecture, so
  15 streams can advance independently until global reduction backpressure

The minimum slot count is a functional point, not an assumed optimum. The
composed performance model and RTL must sweep source and destination slot depth
under the measured global-reducer ready schedule.

## Equivalence Gate

For every accepted group, the decoder output must equal the local reducer's 128
canonical 419-bit beats exactly. The test records descriptor handshakes, SRAM
requests and responses, writes, packet completions, codec flits, and output
beats. RTL and the finite endpoint performance model must agree on packet/flit
counts, completion order, stalls, and maximum slot occupancy.

SRAM is initially an inferred synchronous word array for control and schedule
closure. Its bitcell area and energy must later be substituted from a cited
macro model; the inferred array is not itself a physical SRAM PPA claim.
