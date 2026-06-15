# Composed Dual-Stream Attention No-Hash Softmax Pipe1

This design keeps equivalence-only hash folding disabled and inserts one register stage on the shared softmax score input. The value-stream payload and score-mix inputs are delayed by two stages, accounting for the new input register plus the existing registered softmax weight output.

The point is intended to test whether the no-hash critical path from `seed_state` into `u_softmax/weights[...]` is removable by ordinary pipeline staging.
