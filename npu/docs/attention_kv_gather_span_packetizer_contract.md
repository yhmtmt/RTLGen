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
destination, and canonical addresses normally advance by 256 bytes per
accepted packet. A full 128 KiB consume descriptor for K instead maps the
index as `block[5:0], stream, packet_in_block[1:0]`. This emits each stream-0
1 KiB block immediately before its matching stream-1 block while covering the
same address set exactly once.
The eight-bit transport tag is the low byte of the packet index. Tag reuse is
safe only with a bounded receive window and ordered packet retirement; the
downstream composition must enforce that condition.

`cmd_descriptor_last` marks the final packet of a span.
`cmd_schedule_last` additionally requires the input span to be the final
schedule descriptor. Commands and metadata remain stable while downstream
`ready` is low. A completing span can be replaced in the same cycle.

## Llama7B Scale

The exact transient-residency schedule expands as follows:

- 49,472 gather spans in executable group-major, block-paired K order;
- 17,055,744 total packet commands;
- 16,777,216 HBM-source packets;
- 16,777,216 canonical-consume packets;
- 278,528 resident-refill packets.

The RTL equivalence test replays a 1 MiB full tile, a full block-paired K
plane, a 16 KiB resident-tail span, and a 112 KiB HBM-tail span under
backpressure. These exercise 5,120 commands including the 4,096-packet
terminal-index boundary. Full-schedule
counts are checked analytically from every exact descriptor without requiring
a 17-million-command RTL simulation.

## Remaining Boundary

Receive-before-transmit installation, concurrent dispatch, shared-mesh
movement, canonical ejection, per-destination descriptor ordering, and
automatic target/control adaptation into the exact K/V transposers are now
composed. The external HBM controller and PHY remain outside the design
boundary.
