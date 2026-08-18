# Score32 Exact Aligned Transport Codec Contract

This codec is the field-preserving transport anchor between one local temporal
reducer output and the 256-bit segmented NoC payload path. It carries the full
exact-partial aggregate state without narrowing or recomputation.

## Aggregate Beat

The canonical 419-bit aggregate beat uses the same least-significant-bit-first
layout as `npu.eval.gqa8_compositional_exact`:

| Bits | Field |
|---|---|
| `15:0` | command ID |
| `20:16` | head ID |
| `52:21` | signed global maximum |
| `85:53` | exponential sum |
| `89:86` | value slice |
| `90` | last slice |
| `418:91` | eight signed 41-bit weighted numerators |

The field widths are therefore `16 + 5 + 32 + 33 + 4 + 1 + 328 = 419`.
The codec treats the complete beat as bits; signed interpretation remains at
the reducer interfaces.

## Aligned Flits

- Flit 0 carries aggregate bits `255:0`.
- Flit 1 carries aggregate bits `418:256` in payload bits `162:0`.
- Flit 1 payload bits `255:163` are zero.
- Each accepted aggregate beat produces exactly two accepted flits in order.
- A new aggregate beat is not accepted until the retained two-flit transfer
  can no longer be overwritten.

The decoder accepts exactly the same two phases, rejects nonzero padding or an
invalid phase/last sequence with a sticky protocol error, and presents one
stable aggregate beat until its consumer accepts it. Reset discards any
partially transferred beat on either side.

## Ready/Valid Composition

The encoder input connects directly to the local temporal reducer `out_*`
interface. Its output is packetized as an ordered two-flit payload. At the root,
the depacketized decoder output connects directly to one global-tree `leaf_*`
interface. Backpressure must propagate through every retained stage; a static
release timestamp is not equivalent to this contract.

The endpoint descriptor still provides packet identity, source, destination,
VC, tag, fragment, and packet-last metadata. Codec phase is subordinate to that
framing and must agree with fragment order. NoC transport must not infer a new
aggregate boundary from payload values.

## Closure Limits

Standalone round-trip equivalence closes field preservation and backpressure,
not the full Phase-2 schedule. The next composition must drive codec input from
actual local-reducer validity, route through the endpoint/mesh, and drive the
root tree under its actual readiness. Shared K/V traffic must separately use
SRAM-residency-driven release. HBM/DRAM control remains external by design.
