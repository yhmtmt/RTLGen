# Canonical ingress to cluster adapter: implementation contract

This contract records the next integration boundary from the existing RTL ports.
It is not evidence of an implemented adapter or permission to recost the frontier.

Source: `attention_kv_capacity_gather_mesh_ingress` emits per-endpoint valid/ready,
layer, tile, 20-bit canonical tile-byte address, and 256-bit data.

| Consumer control | Canonical derivation or ownership |
|---|---|
| K versus V | address bit 19: zero selects K, one selects V |
| KV head | address bits 18:17 |
| Wave | tile bits 6:4 |
| V stream | address bit 16 |
| V block slot | address bits 15:10 |
| V fill head base | KV head multiplied by eight |
| V fill buffer | wave parity, subject to endpoint target acceptance |
| Destination endpoint | `(3 * layer + tile[3:0]) mod 16`, as implemented by the gather scheduler |
| Command identifier | explicit scheduler ownership; not derivable merely by concatenating address bits |

The K consumer is `attention_score32_exact_kv_key_pingpong_ingress`. It needs a
head fill-target handshake and independently supplied query writes before its
command can release producer query/key beats. Canonical K bytes alone do not
establish query residency or command readiness.

The V consumer is `attention_score32_exact_kv_value_ingress`. One accepted fill
target owns an entire head and requires 128 accepted block targets. Each block
transposes 1 KiB into sixteen 512-bit endpoint rows. The adapter must wait for
target acceptance before offering its data and retain metadata through endpoint
backpressure. A head boundary must not overwrite an active target.

Verification must cover both p53 and p54 consumers, every byte of representative
full K and V heads, split resident/HBM plane continuity, repeated wave/head
transitions, and independent downstream stalls. Assert no dropped, duplicated,
or prematurely consumed bytes, and verify the upstream ready chain. Include a
nonzero layer to exercise destination rotation. Canonical full-flit validity
must be justified from descriptor alignment and length before tying all 32 byte
valid bits high; the ingress ports do not expose a byte-valid mask.

After this functional composition, characterize the selected V buffering and
SRAM implementation and measure the complete data-dependent schedule. The
historical VC0 stream used by the release-cadence mesh test remains a separate
transport workload and cannot supply this adapter's address contract.

## K delivery-order gap

Source inspection exposes an additional ordering requirement. The span
packetizer emits `canonical_base + packet_index * 256`; a full K plane is
therefore delivered in ascending address order. The ping-pong K transposer
retains one active block slot until both streams supply its 64 input flits.
Its existing test deliberately iterates block slot before stream.

For head zero, the first 32 ascending flits cover addresses 0x00000 through
0x003e0 (stream zero, slot zero). The next ascending flit at 0x00400 selects
slot one, while the transposer still needs stream one's slot-zero flits at
0x10000 through 0x103e0. That violates its active-target match. Two ping-pong
buffers alone do not implement arbitrary head-plane reordering.

Before connecting these ports, embody paired-block gather ordering or a sized
reorder store, including the split resident/HBM ranges and destination ordering
locks. Verify the resulting full-head RTL delivery, and include its buffering,
descriptor, and service costs in the eventual PPA/performance comparison.
`tests/test_kv_gather_key_ordering.py` reproduces the boundary directly in RTL:
the first 32 ascending flits pass, the 33rd at 0x00400 raises protocol error,
and a matching second-stream flit at 0x10000 is accepted without error. Both
diagnostic cases pass. Full gather-to-transposer composition and a corrective
implementation remain pending.

The corrective primitive `attention_kv_paired_head_schedule.sv` now emits all
128 alternating 1 KiB spans for a K head. Its model preserves byte coverage and
resident/HBM ownership for zero, 16 KiB, and full-head resident prefixes. RTL
tests cover stalls and invalid prefixes. `test_paired_schedule_key_transpose.py`
connects the sequencer to p53 and p54 transposers and checks 4096 input flits
and all 4096 numerical output beats under downstream stalls for each case.
The fixture now varies bytes by block slot, stream, token lane, and dimension,
and checks every output byte for p53 and p54 across all four KV heads (eight
tests pass). It also checks producer/block assignment, head, dimension-pair,
last, and the stability of data and metadata through stalls. This catches
permutations that the earlier block-constant fixture could not distinguish.
It does not exhaust arbitrary tensor values or validate the downstream K/Q stage.

The standalone primitive's `head_done`
pulse means the final span was accepted, not that remote writes or K/Q staging
completed. Source-base adaptation, receive-before-transmit descriptor ordering,
and completion barriers must preserve that distinction in the integration.

The paired-span option increases K descriptors to 65,536 per layer. With the
existing V and refill descriptors, the total is 66,062 per layer and 2,113,984
over 32 layers, requiring at least 17-bit layer and 22-bit model counters.
These are control-work counts, not measured latency or PPA. The existing
aggregate counter widths cannot be reused without a range audit.

`addressed_key_spans` in `npu/sim/perf/attention_kv_paired_gather.py` now supplies
an executable source-address oracle for integration. The exhaustive test visits
all 2,097,152 K spans across 32 layers, 128 tiles, and four heads, checking
canonical coverage, source ownership, resident bounds, and endpoint selection.
Tile 2 uses packed 16-KiB head prefixes in the resident cache, rather than
the HBM layout's 128-KiB head stride. The full-model K consume coverage is
34 MiB resident plus 2014 MiB HBM. Eleven model tests pass. These address checks
alone do not establish RTL source-address equivalence.

The standalone `attention_kv_paired_key_address.sv` adapter now matches this
oracle for all 2,097,152 K spans in `tests/test_paired_key_address.py` (passed).
The comparison includes canonical address, 34-bit source address, resident/HBM
selection, source endpoint, and destination cluster. Unaligned offsets are
also rejected. The adapter is combinational: it does not own valid/ready or
retain coordinates during a stall. Connecting it to the paired sequencer and
capacity scheduler, widening counters, and enforcing completion ordering remain
integration requirements. No composed transport latency or physical cost is
established by the exhaustive address test.

The capacity scheduler now has an explicit `PAIRED_K=1` integration mode. It
retains the group/wave/tensor/tile traversal, replaces each K head with 128
paired 1-KiB spans, and uses the verified address adapter. Its descriptor count
widens to 22 bits in that mode. `test_paired_capacity_gather_scheduler.py`
compares all 2,113,984 descriptors (including unchanged V and refill rows)
against the model with two-cycle backpressure windows, checks stability through
acceptance, and verifies the final descriptor and terminal count. That test and
the legacy scheduler and mesh-elaboration tests pass (three tests total).

The mesh wrapper still selects the legacy default (`PAIRED_K=0`). This is a
comparison baseline, not the corrected ingress path. Before switching it, its
aggregate and lane counters must be widened and paired span completion through
the destination ownership guard must be verified. A segment identifies the
head/source partition, not a unique paired span; repeated segment values must
not bypass the guard's terminal-packet completion rule. The scheduler's `done`
continues to mean descriptor acceptance, not downstream numerical completion.

The mesh wrapper now exposes `PAIRED_K=1` and propagates 22-bit descriptor counts
through the scheduler, destination guard, packet submission telemetry, and all
16 packetizer lanes. Widths are derived locally from the mode; the legacy
default retains its original interface widths. Both modes elaborate without
port-width mismatch warnings. The widened guard regression performs 66,003
actual descriptor completions, crossing the old 16-bit boundary while
alternating sources and reusing terminal tag 3. A next descriptor for the same
destination remains blocked during delayed completion. This verifies the
guard's ownership rule independently of the mesh. Paired payload delivery
through the wrapper into the transpose buffer remains unverified, so the
legacy default has not been switched and no composed PPA claim is made.
