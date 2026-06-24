# Llama7B Mixed/Int8 Native Attention Quality

This proposal evaluates whether the current mixed/int8 softmax-recip latency
frontier keeps next-token rankings on a real 7B-class checkpoint when the
attention modules are shadowed with the same q8/k8/v8 and int8 reciprocal
softmax approximation used by the hardware candidate.

The result is a precision gate for the mixed/int8 frontier. It is not QAT, full
perplexity, or task accuracy.

