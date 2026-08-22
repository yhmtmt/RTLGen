# Phase-2 Shared-SRAM Stream Transport Contract

This contract defines the exact transport boundary for the shared-SRAM part of
the checked Llama7B Phase-2 schedule.  It replaces the historical synthetic
`data_seed` payload with address-preserving SRAM transfers.  It does not reuse
the retracted reduction traffic; exact reducer-to-root traffic remains a
separate VC1 composition.

## Canonical Regression Quantities

- mesh endpoints: 16
- logical waves: 8
- local-only wave: 4
- remote contexts: `7 waves x 16 destinations = 112`
- payload per context: 17,408 bytes
- packets per context: 68
- payload per packet: 256 bytes
- flits per packet: 8
- flit width: 256 bits / 32 bytes
- total remote packets: 7,616
- total remote flits: 60,928
- shared-stream virtual channel: VC0

These quantities reproduce the historical fractional-smear placement only.
For destination cluster `c`, that policy chooses source endpoint `(c +
shift[wave]) mod 16`, where `shift = [4, 7, 10, 13, 0, 3, 6, 9]`.  Wave 4 is
local and must not be admitted to the mesh.

The 112 remote contexts are not implied by 68 MiB of capacity.  Whole-token
or whole-tile residency can produce fewer, larger contexts, and a
capacity-balanced locality-aware assignment can make resident contexts local.
The hardware interface therefore supports a layer-specific expected remote
context count, explicit source endpoints, and a variable positive packet
count up to its elaborated maximum.  A layer with zero remote contexts
completes admission without using this transport.

## Producer and Residency Boundary

A readiness event means that the complete declared source window is resident
in source SRAM and that its source base address is stable.  The admission
scheduler accepts readiness independently for all 16 clusters and emits one
context command at a time.  It must not create release timing or derive a
placement policy.

The context command carries:

- wave index
- source endpoint
- destination endpoint
- source byte base address
- destination byte base address reserved by the consumer
- packet count

At most one live context may own a source endpoint and at most one may own a
destination endpoint.  These resource rules allow up to 16 contexts to run in
parallel without descriptor-port arbitration and prevent address-slot reuse
while packets remain in flight.

## Packet and Address Mapping

For packet index `p` in `[0, packet_count)` and fragment index `f` in `[0, 7]`:

```text
tag             = p
TX byte address = source_base      + 256*p + 32*f
RX byte address = destination_base + 256*p + 32*f
last            = (f == 7)
```

The canonical regression uses `packet_count = 68`.  Larger whole-tile
contexts reuse the eight-bit wire tag as `p mod 256`; ordered completion and
the bounded eight-packet live window must prove that an earlier packet with
the same tag has completed before reuse.

Each packet's RX descriptor must be accepted before its TX descriptor may be
exposed.  A context may have at most eight installed, incomplete packet
contexts, matching the endpoint's bounded RX context table.  Packet tags are
unique within a live `(source, destination, VC0)` stream.  A tag may be reused
by a later context only after every packet of the previous context has
completed and the context completion has been accepted.

The endpoint writes each flit directly to destination SRAM.  No packet-wide
register reassembly buffer is permitted.

## Completion and Consumer Ownership

Packet completion means that the final flit write for that packet was
accepted by destination SRAM.  Context completion is emitted only after all
declared packet completions have been validated in order.  Context completion must
remain valid and stable under backpressure.

Acceptance of context completion is the destination consumer's residency
acknowledgement.  Only that handshake releases the source and destination
endpoint ownership and permits either address window to be reused.  The mesh
and packet endpoint do not independently release a logical context.

## GQA8 Tensor Layout

The semantic payload for one complete 1024-token Llama7B GQA8 tile is 1 MiB.
It contains four KV-head regions in ascending KV-head order.  Each 256 KiB
head region contains:

1. 128 KiB of K data ordered by stream, 8-token block slot, then head
   dimension.  Each 64-bit K beat holds the eight token lanes for one
   dimension.
2. 128 KiB of V data ordered by stream, 8-token block slot, then 8-dimension
   slice.  Each 512-bit V row holds an 8-token by 8-dimension matrix in
   token-major byte order.

The executable definition is
`npu/sim/perf/attention_shared_sram_gqa8_tensor_layout.py`.  It is the sole
byte-offset authority for producer K beats and local value-SRAM fill rows.
Shared 1024-bit words are interleaved over the 17 physical macros in each
4.25 MiB home by `bank = word_index mod 17` and
`row = floor(word_index / 17)`.

One shared word holds sixteen K dimension beats for one token block.  A
complete dimension window therefore contains 128 words, or 16 KiB.  With 17
single-read-port banks it has an eight-cycle conflict-free lower bound.  A
two-window prefetch buffer can overlap that fetch with the corresponding
sixteen compute cycles.  The full two-window register realization is
functionally checked but synthesis-intractable.  The bounded alternative uses
two 17-word round windows and exposes sixteen dimensions over eight rounds;
its exact contract and current physical-evidence boundary are recorded in
`npu/docs/attention_shared_sram_k_window_scheduler_contract.md`.  The bounded
17-bank hierarchy now completes generic Nangate45 mapping with zero structural
problems, but routed PPA is still required; a single shared-macro adapter
cannot supply all 53/54 dual-stream producers.

## Equivalence Boundary

Transport equivalence must compare the complete declared source and
destination windows, plus wave, source, destination, packet count, packet ordering, and
completion identity.  Hashes may be used as a compact diagnostic only when
the test also proves every expected address was written exactly once and no
unexpected address was written.

The transport window is no longer semantically opaque: every byte has a K or
V coordinate under the layout above.  RTL composition with the banked K
prefetch scheduler and local value-SRAM fill consumer remains a required
gate.  The existing GQA8 probe also drives only one accepted dimension beat
per block even though the compute RTL supports accumulation until
`input_last`; it must be upgraded to all 128 dimensions before this evidence
is presented as end-to-end exact Llama7B attention equivalence.

## Physical Accounting Boundary

The controller, packet endpoints, mesh, and concurrent transfer-window SRAM
ports are synthesizable RTL.  The full shared-SRAM capacity is accounted from
the checked CACTI/macro registry; it must not be replaced by resettable state
registers or by a fabricated full-capacity RTL array.  Physical reports must
state separately:

- transport/controller standard-cell area and power
- endpoint and mesh area and power
- concurrent source/destination window macro area and access energy
- full shared-SRAM capacity macro area and access energy

HBM/DRAM service and its controller remain external.
