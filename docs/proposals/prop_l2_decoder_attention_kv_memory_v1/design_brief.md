# Design Brief

The previous decoder-stage result showed that ranker-only work is not enough to explain decoder-scale behavior. Attention becomes dominant in long-context resident-weight cases, while MLP and output projection remain important in streaming-weight cases.

This job keeps the sweep broad and rough:

- memory tiers: `local_sram`, `shared_sram`, `hbm`, `remote_hbm`
- network sensitivity: non-local KV tiers use a NoC-hop effective bandwidth bound
- KV sharing: `mha`, `gqa4`, `mqa`
- KV precision: 8-bit and 16-bit cache traffic
- context lengths: 128 through 32768 tokens
- model shapes: GPT-2-like through larger long-context proxies

The report should identify whether the attention frontier is primarily compute, KV movement, score/softmax movement, or memory/network locality.
