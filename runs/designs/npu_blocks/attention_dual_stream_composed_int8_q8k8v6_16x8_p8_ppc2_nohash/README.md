# Composed Dual-Stream Attention No-Hash PPA Block

This design point matches the Q8/K8/V6 dual-stream composed attention datapath
but disables equivalence-only hash folding for physical PPA measurement.

The generated top exposes softmax weights, value accumulators, and score mixes
directly so synthesis preserves the datapath without timing artificial
`result_hash` or `weight_hash` logic.
