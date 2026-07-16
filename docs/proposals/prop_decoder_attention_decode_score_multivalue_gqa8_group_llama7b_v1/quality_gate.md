# Quality Gate

The candidate retains the merged signed-int8 Q/K/V, signed-32 score,
global-max two-pass LUT-softmax, signed 41-bit numerator, and rounded iterative
division contract. It does not change model precision.

The existing Llama7B mixed-int8 generation-quality result remains the precision
gate. This proposal adds no approximation parameter and therefore must not
claim a new quality improvement or degradation. Any future folded-head or
reduced-precision variant must pass its own equivalence and generation-quality
gate before it can replace this exact GQA8 point.
