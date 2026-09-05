# Macro-Banked Llama7B RMSNorm Phase-3 Physical Anchor

This proposal replaces the synthesis-infeasible inferred-register row/gamma
storage with the exact 64-macro organization defined in
`npu/docs/llama7b_rmsnorm_banked_storage_contract.md`.

The conservative implementation deliberately permits one outstanding macro
read. Its measured no-stall row latency is 1800 cycles, versus 776 cycles for
the rejected register-storage schedule. This is the first trustworthy physical
baseline; response buffering and pipelined reads belong in a later measured
Pareto comparison.
