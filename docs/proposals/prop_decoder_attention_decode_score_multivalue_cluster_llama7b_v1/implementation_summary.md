# Implementation Summary

The composed RTL contains one M1x8 signed-int8 score producer, one 16Kx256
score-bank proxy, and one 128-dimensional two-pass reducer. Each score row is
requantized and written once per eight-token block. During replay, the score
row is read once, eight LUT weights are retained, and sixteen addressed 8x8
value matrices update sixteen banks of eight signed 41-bit numerators.

The weighted-value datapath contains one physical 8x8 multiply/reduce block;
the value-slice index selects the accumulator bank and does not replicate the
64 multipliers. Accumulators clear over sixteen cycles to avoid a single wide
clear fanout. One iterative divider emits sixteen backpressured 320-bit result
beats instead of exposing a 5,120-bit result port.

The equivalence probe checks score rounding and saturation, value-response
latency, input stalls, result backpressure, all 128 final dimensions, one
score-bank read per block, and sixteen ordered value requests per block.
