# Exact K/V Gather Span Packetizer Contract

## Function

`attention_kv_gather_span_packetizer` converts one aligned contiguous gather
span into ordered 256-byte packet commands. Each packet contains eight
32-byte mesh flits. It preserves the layer, tile, segment, operation, source,
destination, K/V plane, canonical address, and resident-cache destination
metadata required after transport.

The input and all three base addresses must be 256-byte aligned. Payloads must
be positive multiples of 256 bytes and cannot exceed 1 MiB. Invalid spans fail
closed with a sticky protocol error. The exclusive end address must also fit
the 20-bit canonical tile space and both 34-bit physical address spaces.

## Ordering And Backpressure

Packet indices increase from zero through `payload_bytes / 256 - 1`. Source,
destination, and canonical addresses advance by 256 bytes per accepted packet.
The eight-bit transport tag is the low byte of the packet index. Tag reuse is
safe only with a bounded receive window and ordered packet retirement; the
downstream composition must enforce that condition.

`cmd_descriptor_last` marks the final packet of a span.
`cmd_schedule_last` additionally requires the input span to be the final
schedule descriptor. Commands and metadata remain stable while downstream
`ready` is low. A completing span can be replaced in the same cycle.

## Llama7B Scale

The exact transient-residency schedule expands as follows:

- 4,896 gather spans;
- 17,055,744 total packet commands;
- 16,777,216 HBM-source packets;
- 16,777,216 canonical-consume packets;
- 278,528 resident-refill packets.

The RTL equivalence test replays a 1 MiB full tile, a 16 KiB resident-tail
span, and a 112 KiB HBM-tail span under backpressure. These exercise 4,608
commands including the 4,096-packet terminal-index boundary. Full-schedule
counts are checked analytically from every exact descriptor without requiring
a 17-million-command RTL simulation.

## Remaining Boundary

The packetizer emits commands, not payload flits. Receive-before-transmit
descriptor installation, concurrent dispatch across HBM sources and local
owners, shared-mesh movement, and canonical K/V ingress ejection remain in the
next composition step. The external HBM controller and PHY remain outside the
design boundary.
