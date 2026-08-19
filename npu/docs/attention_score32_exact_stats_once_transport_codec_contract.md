# Score32 Exact Stats-Once Transport Codec Contract

This codec is the dense exact-transport candidate for one GQA8 aggregate group.
It removes only metadata that the checked group-major order makes redundant;
all signed 41-bit numerators and exact max/sum fields are preserved.

## Input Group

The encoder receives one group context before aggregate data:

- `command_id[15:0]`
- `head_base[4:0]`, restricted to `0`, `8`, `16`, or `24`

It then accepts exactly 128 canonical 419-bit beats in this order:

1. heads `head_base + 0` through `head_base + 7`
2. slices `0` through `15` for each head
3. `last=1` only on slice 15
4. command ID constant across the group
5. global maximum and exponential sum constant across all 16 slices of a head

Any mismatch sets a sticky protocol error. The canonical aggregate layout is
defined by `attention_score32_exact_aligned_transport_codec_contract.md`.

## Packed Bitstream

Bits are emitted least-significant first. For each head, in order, the stream
contains:

- signed global maximum: 32 bits
- exponential sum: 33 bits
- slice values 0 through 15: `16 x 328` bits

One head therefore contributes `65 + 5248 = 5313` bits. One group contributes
`8 x 5313 = 42504` bits, transported as 167 256-bit flits. Flits 0 through 165
are full. Flit 166 carries the final 8 stream bits in payload bits `7:0`; bits
`255:8` are zero.

`flit_group_last` marks only flit 166. It must never drive the endpoint's
packet `flit_last`: packet boundaries remain descriptor-owned and occur at up
to eight flits, so one group spans 20 full packets plus one seven-flit packet.

## Streaming Hardware

The encoder and decoder use bounded bit reservoirs. They must not instantiate
a 42,504-bit group register. Backpressure is legal at every context, aggregate,
flit, and reconstructed-aggregate interface. Accepted output data remains
stable until consumed.

The decoder receives the same group context out of band from checked command
or packet metadata. It reconstructs all 128 canonical 419-bit beats, repeating
the transmitted max/sum for the 16 slices of each head and restoring inferred
command ID, head ID, slice, and last fields.

## Equivalence Gate

For every valid group:

- reconstructed 419-bit beats equal encoder input beats bit for bit
- accepted flits equal 167
- only final-flit zero padding is discarded
- arbitrary stalls do not drop, duplicate, or reorder data
- malformed order, early/late group-last, nonzero padding, or context mismatch
  sets protocol error
- reset discards partial group state

Standalone equivalence and PPA do not close the local-reducer-to-root path.
The follow-on composition must connect actual reducer validity through the
endpoint/mesh to actual global-tree readiness.
