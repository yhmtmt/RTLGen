# Exact K/V Cluster Ejection Ingress Contract

## Function

`attention_score32_exact_kv_cluster_ejection_control` consumes one ordered
canonical mesh-ejection stream. It derives K fill targets, V fill targets, and
all 128 V block targets directly from the canonical layer, tile, and byte
address. It requires one complete block-paired K plane followed by the matching
stream-major V plane.

`attention_score32_exact_kv_cluster_ejection_ingress` composes that control
with the real ping-pong K transposer, 64-bank wide K/Q stage, and V transposer.
There is no synthetic target source between mesh ejection and either ingress
datapath.

## Wave And Command Identity

One cluster wave contains 4,096 32-byte K flits and 4,096 32-byte V flits for
the same `{layer,tile,kv_head}`. `wave_index` is `tile[6:4]`, `head_base` is
`kv_head << 3`, and `buffer_sel` is `wave_index[0]`.

The local logical command ID is `0x8200 + layer*4 + kv_head`. It is shared by
all 16 clusters and all eight waves of the same layer/head group. The local
command is held until the K stage and external composed score/SRAM cluster both
assert readiness. A 16-lane command barrier waits for matching metadata from
every cluster before committing one command to the generated hierarchy.
The wave-completion counter is 11 bits and is verified through all 1,024
layer/group/wave transactions in one full model pass.

## Ordering And Backpressure

K flits are ordered by `block_slot`, then stream, then the 32 flits of the
1 KiB stream block. V flits remain in canonical stream/block/address order.
The controller holds the first flit while issuing each derived target, then
propagates transposer readiness back to canonical ejection. It rejects any
address, layer, tile, head, or tensor transition that differs from the exact
wave sequence.

The full-wave RTL composition verifies:

- 4,096 accepted K flits and one K head completion;
- 4,096 accepted V flits, 128 automatic targets, and 2,048 V fill rows;
- 8,192 producer K beats for a p53 cluster;
- one atomic K-stage/cluster command with matching metadata;
- 1,024 barrier commits without telemetry wrap;
- ready-valid operation under K, V-target, V-row, and command stalls.

## Remaining Boundary

The 16-lane mesh-to-controller structural wrapper and complete cluster compute
hierarchy composition remain to be generated. The current V transposer has one
buffer, so its fill/drain overlap cost and throughput remain open. Inferred
storage still requires characterized SRAM substitution. The external HBM
controller and PHY remain outside the chip RTL boundary.
