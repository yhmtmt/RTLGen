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
