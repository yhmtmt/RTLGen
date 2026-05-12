# Design Brief

- proposal_id: `prop_l1_decoder_attention_kv_tile_stream_v1`
- title: `Decoder attention/KV tile stream measured RTL anchor`

## Trigger

The merged long-context attention/KV sweep found `qk_score` dominant across all
focus rows. The best long-context configurations used shared SRAM, MQA, 4-bit
KV, and one hop, but even those best cases still showed high KV-limited cycle
share. The next useful step is measured RTL/PPA for the datapath behind that
model.

## Scope

The first source-enabled block should model a single-token decode tile:

- query vector fragment input
- KV stream input
- configurable `head_dim`
- configurable `kv_bits`
- configurable lane count
- configurable stream width in bytes per cycle
- cycle and byte counters for equivalence with a simple perf model

The first measured block should be a macro-style circuit block, not a full chip
or IO-pad model.

## Non-Goals

- full SRAM macro banking
- NoC arbitration RTL
- full softmax/value-mix pipeline
- output projection or ranker integration
- quality analysis of KV quantization

## Proposed Evaluation Sequence

1. Implement and merge the `attention_kv_tile` RTLGen operation and local
   equivalence tests.
2. Dispatch `l1_decoder_attention_kv_tile_smoke_v1`.
3. If the smoke point passes, dispatch `l1_decoder_attention_kv_tile_frontier_v1`.
4. Feed accepted PPA and cycle counters back into the L2 attention/KV estimator.
