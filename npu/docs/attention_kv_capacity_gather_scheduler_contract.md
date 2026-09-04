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

Each layer emits 1,042 descriptors in two ordered phases:

- 10 refill descriptors: two contiguous 1 MiB tiles and eight 16 KiB planar
  spans for the 128-token tail;
- 1,032 consume descriptors ordered by head group, wave, K/V plane, then tile.
  Every ordinary plane uses one 128 KiB descriptor; each of tile 2's eight
  planes uses a 16 KiB resident prefix followed by a 112 KiB HBM suffix.

For each of four GQA head groups, waves 0 through 7 deliver one K plane and one
V plane to each of the 16 destination clusters. This matches the embodied
cluster-SRAM command cadence and its one-`{head_base,wave}`-per-buffer
residency contract. The 32-layer schedule therefore contains 33,344
descriptors. `last` is set only on the final V descriptor of group 3, wave 7.

The superseded 153-descriptor tile-major order had correct aggregate byte
counts but could not drive the cluster SRAM: after `V0,wave0`, it requested
`V1,wave0` in the same buffer while the compute hierarchy required
`V0,wave1`. It remains historical traffic accounting, not executable
scheduling evidence.

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
all 33,344 emitted descriptors against the model under backpressure and checks
that stalled descriptors remain stable.

## Remaining Boundary

Packetization, shared-mesh routing, payload movement, and per-destination
descriptor ordering are composed. Ordered canonical ejection still requires
automatic target/control adaptation into the exact K/V transposers. V
fill/drain overlap and characterized SRAM substitution remain open. The
external HBM controller and PHY are intentionally outside the design boundary.
