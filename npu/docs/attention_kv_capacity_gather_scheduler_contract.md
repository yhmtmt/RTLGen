# Exact Llama7B K/V Capacity Gather Scheduler Contract

## Scope

`attention_kv_capacity_gather_scheduler` emits the exact contiguous byte-span
descriptors needed to gather one int8 Llama7B GQA K/V cache with 32 layers,
128 tiles per layer, 1,024 tokens per tile, four K/V heads, and a head
dimension of 128. The canonical 1 MiB tile layout is
`K[head][token][dimension]` followed by `V[head][token][dimension]`.

The current baseline uses 68 MiB of **transient** shared SRAM. Each layer owns
2,228,224 bytes: two complete tiles plus the first 128 tokens of tile 2. The
resident ranges are refilled from HBM on every decode, so this organization
does not claim a reduction in HBM read traffic. Persistent residency is a
separate policy and is not selected by this RTL.

## Descriptor Sequence

Each layer emits 153 descriptors in two ordered phases:

- 10 refill descriptors: two contiguous 1 MiB tiles and eight 16 KiB planar
  spans for the 128-token tail;
- 143 consume descriptors: two resident full tiles, sixteen alternating
  resident/HBM spans for tile 2, and 125 direct-HBM full tiles.

The tile-2 consume order is monotonically planar. For each of eight K/V head
planes, a 16 KiB resident prefix is immediately followed by its 112 KiB HBM
suffix. The 32-layer schedule therefore contains 4,896 descriptors. `last` is
set only on the final consume descriptor.

Every descriptor identifies the layer, tile, tile-local segment, operation,
source kind and endpoint, destination cluster, K/V plane, canonical tile
address, source and destination byte addresses, and payload length. A
descriptor remains stable while `valid` is asserted and `ready` is low.

## Placement And Traffic

Tile ownership is `(layer * 3 + tile) % 16`. Every complete 16-tile wave sends
one tile to each cluster, and every cluster consumes exactly 8 MiB per layer.
Resident data is owner-local. Direct and refill HBM spans enter through four
explicit corner endpoints: 0, 3, 12, and 15.

Per layer, the scheduler accounts for:

- 2,228,224 resident refill bytes;
- 2,228,224 resident consume bytes;
- 131,989,504 direct-HBM consume bytes;
- 134,217,728 total HBM source bytes;
- 134,217,728 canonical consume bytes.

The Python model checks these conservation identities. The RTL test compares
all 4,896 emitted descriptors against the model under backpressure and checks
that stalled descriptors remain stable.

## Remaining Boundary

Descriptors represent contiguous spans, not NoC packets. Span-to-packet
expansion, shared-mesh routing, returned payload movement into canonical K/V
ingress, and end-to-end backpressure remain to be composed. The external HBM
controller and PHY are intentionally outside the design boundary.

