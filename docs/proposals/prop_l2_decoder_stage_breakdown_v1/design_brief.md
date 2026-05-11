# Design Brief

Estimate a coarse single-token decoder-stage breakdown before deeper producer/ranker RTL work.

The model separates two bounding assumptions:

- `streaming_weights`: decoder and output-projection weights are served each token.
- `resident_weights`: weights are local or prefetched, exposing compute and KV-cache traffic.

The goal is to quickly see whether the ranker frontier matters at decoder scale, or whether attention/KV movement, MLP, or output projection dominates first.
