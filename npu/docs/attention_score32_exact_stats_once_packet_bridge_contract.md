# Score32 Exact Stats-Once Packet Bridge Contract

This bridge connects one exact stats-once codec stream to one 256-bit segmented
NoC endpoint port. It embodies packet boundaries and checked transport metadata
without changing the 42,504-bit group payload.

## Group Context

Before accepting payload, the transmit bridge accepts:

- `command_id[15:0]`
- `head_base[4:0]`, restricted to `0`, `8`, `16`, or `24`
- `source[3:0]` and `destination[3:0]`
- `vc[1:0]`
- `group_epoch[2:0]`

The receive bridge is armed independently with the same expected context. The
command scheduler is responsible for installing receive context before transmit
release. Command ID and head base remain scheduler metadata for the root codec;
they are not redundantly inserted into every payload flit.

## Packet Mapping

One group is exactly 167 flits:

- packets 0 through 19 contain eight flits each
- packet 20 contains seven flits
- `fragment` runs from 0 through 7, or 0 through 6 on packet 20
- packet `last` is asserted on fragment 7 or on the final group flit
- `tag = {group_epoch[2:0], packet_index[4:0]}`

Only one group per source may be in flight for a given epoch. A source must not
reuse an epoch until the scheduler has observed completion, preventing the
eight-epoch tag space from aliasing live traffic.

`group_last` belongs to the codec stream and is asserted only on group flit
166. NoC `last` belongs to each packet. The bridge must never directly connect
these two signals.

## Ready/Valid and Validation

Both directions are fully backpressured. Metadata and payload remain stable
while valid is asserted and ready is low. The transmit bridge rejects early or
late codec `group_last`. The receive bridge checks destination, source, VC,
tag, fragment, packet-last position, packet order, and the exact 167-flit group
length. Violations set a sticky protocol error and cannot create a clean group
completion.

The receive output reconstructs the original flit stream bit for bit, emits
`group_last` only for flit 166, and retains `command_id` and `head_base` as
stable outputs for the root codec. Context becomes reusable only after that
output flit is consumed.

## Scope Boundary

The first composition drives these bridges directly into
`noc_segmented_mesh4x4` to prove packet and route equivalence. It does not yet
claim SRAM endpoint closure. The follow-on must place packet-sized inferred
SRAM buffers and `noc_sram_packet_endpoint` descriptor/read/write control at
the same boundary, then scale from one checked source to the 15 remote sources
feeding the root exact reduction tree.
