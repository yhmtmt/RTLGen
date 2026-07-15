# Quality Gate

The candidate retains the merged signed-int8 Q/K/V, signed-32 score,
global-max two-pass LUT-softmax, signed 41-bit numerator, and rounded iterative
division contract. It changes sharing and transport, not precision.

Promotion to physical evaluation requires all of the following:

1. Every RTL result slice equals the integer performance-model result for all
   128 output dimensions.
2. Rounding, signed-32 saturation, stalls, value latency, and output
   backpressure pass.
3. The trace contains exactly one score write and one score read per block,
   followed by sixteen ordered value-slice requests.
4. Equivalence hashes remain probe evidence and are absent from measured RTL.

The existing Llama7B mixed-int8 generation-quality result remains the precision
gate because no arithmetic format changes in this proposal.
