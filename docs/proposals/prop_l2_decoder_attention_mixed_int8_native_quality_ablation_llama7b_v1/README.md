# Llama7B Mixed/Int8 Native Quality Ablation

This proposal diagnoses the native-checkpoint quality failure observed for the
mixed/int8 latency frontier by running a small precision ladder on the same
7B-class checkpoint and prompt gate.

The goal is to identify whether the promotion blocker is mainly QKV
quantization, score quantization, or the RTL int8 reciprocal-softmax
approximation.

