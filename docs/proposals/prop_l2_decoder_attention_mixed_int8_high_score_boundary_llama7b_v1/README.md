# Llama7B Mixed/Int8 High Score Precision Boundary

This proposal extends the native checkpoint score precision boundary after the
score10/12/14/16 sweep did not recover the mixed/int8 attention quality gate.

The output should determine whether QKV8 can pass with score18/20/22/24
quantized attention scores, or whether the practical frontier must keep
attention scores and softmax at near-full precision.
