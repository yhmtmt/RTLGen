# Canonical ingress to cluster adapter: implementation contract

This contract records the integration boundary from the existing RTL ports and
the incremental evidence below. Historical gap descriptions are followed by
their implemented checks; they must not be read as the current closure status.
The bounded K path is implemented and tested as described below. V integration,
live score production, full-model execution, and physical recost remain open.

## Canonical full-transport gate in progress

`test_canonical_refill_mesh_and_kq_stage` now drives the real layer-0 refill,
resident/HBM gather, paired mesh, transpose, and wide K/Q stage with canonical
tensor sidecars for tiles 0, 1, and 2, head group zero. Its independent producer
oracle uses canonical tensor coordinates and the rotated slot assignment;
checks compare all accepted Q/K/last words under producer backpressure.
Both p53 and p54 full simulations are pending: no pass or timing claim is made.
The short canonical query-initialization checks pass for both families (two
tests, 31.07 seconds), and the legacy counterparts pass (two tests, 10.54
seconds). CI includes both short gates, not the long transport simulations.

This gate uses deterministic int8 tensors, not pretrained model inputs. Its
consumer is the K/Q stage interface, not the arithmetic score producer. Even a
passing result would not establish V delivery, nonzero-layer mesh rotation,
live numerical reduction, full-model cadence, activity-backed power, or a new
physically credible Pareto point.

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
It does not exhaust arbitrary tensor values or close the full mesh-to-producer path.

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

The bounded p53 and p54 wrapper transport runs have now passed: real layer-0
refill followed by the first K heads of tiles 0, 1, and 2, including the
resident/HBM split, delivers 12,288 paired flits and transpose beats with all
394 descriptors completed. See `paired_transport_validation.md` for scope,
fixture identity, and limitations. Stronger integrated nonuniform-payload runs
also pass for p53 and p54. Both corrected continuous mesh-to-wide-K/Q-stage
runs now pass all 24,576 producer-facing beats per family.
A combined 47-test regression covering addressing, scheduling,
packetization, ownership, legacy mesh behavior, transpose, and closure-matrix
checks also passes. This is not full-model or downstream K/Q equivalence.

The all-head paired-sequencer/transpose test now additionally connects the
wide K/Q stage. Across p53 and p54 and all four heads it fills query memory,
writes all 4096 transpose beats, then checks every producer-facing K and Q
beat and block terminal flag under independent producer stalls. Each head
checks 8192 accepted producer beats (64 blocks times 128 dimensions), including
the rotated extra-block assignments. All 16 cases pass: eight standalone
transpose cases and eight transpose-to-stage cases. This closes that local
interface for the deterministic tensor fixture, not the single composed
mesh-to-stage-to-score-producer execution or full-model equivalence.

## Arithmetic stress fixture versus resident queries

The existing exact-cluster `_stream_block_beats` oracle in
`probe_attention_score32_exact_local16_global_tree_gqa8.py` deliberately varies
Q with cluster, producer, wave, stream, and block index. Five scope-regression
cases check that variation across all 128 dimensions. Those Q streams are
not the resident decoder-query contract: for one decode token and head group,
the same Q must be reused across token placement, waves, and both K streams.
The wide K/Q stage embodies that reuse and duplicates its eight-head Q word
across the two streams.

Therefore, replaying the sixteen collected stress-fixture leaf streams through
the mesh must not be promoted as proof that the resident K/Q stage drives the
same workload. Retain that adversarial arithmetic gate, but add a distinct
canonical tensor fixture whose Q depends only on decode token, head, and
dimension; whose K/V depend on their canonical token coordinates; and whose
producer streams are derived through the real mapper and ingress path. The
direct query-residency mismatch is an input-fixture distinction, not evidence
that the K/Q hardware should accept per-producer or per-stream decoder queries.

`npu/sim/perf/canonical_attention_fixture.py` now provides that separate tensor
source. Q identity includes layer, decode token, global query head, and
dimension; K/V identity includes layer, tensor, KV head, canonical cache token,
and dimension. Deterministic SHA-256 sampling supplies int8 stress values
without encoding placement into tensor identity. It is not pretrained-model
data or a generation-quality result. Producer streams use the actual rotated
slot/block assignment and duplicate the resident eight-head Q word.
Ten tests pass, covering all heads for both producer families, query reuse
over every emitted beat, K memory/producer correspondence at four dimension
boundaries for every block/lane, and unchanged cached K/V across decode-token
changes. This source is not yet wired into the full collected numerical RTL
replay; it establishes a consistent input contract for that next integration.

The canonical source now drives the paired-sequencer/transpose/wide-K/Q RTL
test for all four head groups and both producer families. Each case loads
canonical K memory flits and one resident Q array, then checks every accepted
producer-facing K/Q/last beat against sidecars generated independently by
`CanonicalAttentionFixture.producer_stream`. All 24 cases pass (16 prior
pattern cases plus eight canonical cases); the canonical cases check 65,536
producer beats in total under independent producer stalls. This verifies the
canonical tensor-to-local-K/Q interface at tile 2, layer 7. It does not yet
run those same tensors through real refill/mesh, score production, full-model
mapper lowering, or routed/activity evaluation.
