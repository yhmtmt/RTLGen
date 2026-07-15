# Implementation Summary

The implementation uses the operational dense stream generator with an
explicit packed-score-row result mode restricted to `array_m=1`. The scalar
mode remains backward compatible. The packed mode exposes eight signed 32-bit
scores in the exact lane order consumed by `attention_two_pass_stream_iterdiv`.

Two checked-in configs provide identical M1x8 arithmetic with scalar and packed
result interfaces for direct PPA comparison.

The focused local simulation covers signed operands, final-beat inclusion,
packed lane order, result backpressure, and clean command reuse. The remote
equivalence item remains the authoritative promotion gate.
