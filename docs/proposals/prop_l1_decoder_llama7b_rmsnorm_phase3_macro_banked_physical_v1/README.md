# Macro-Banked Llama7B RMSNorm Phase-3 Physical Anchor

This proposal replaces the synthesis-infeasible inferred-register row/gamma
storage with the exact 64-macro organization defined in
`npu/docs/llama7b_rmsnorm_banked_storage_contract.md`.

The conservative implementation permits one outstanding macro read and takes
1800 no-stall cycles. A second candidate reserves the three slots in the
existing elastic arithmetic pipeline as response credits, permits pipelined
macro reads, and passes the same exact schedule gate at 1035 cycles. Both use
the same 64 macros; their matched routed sweep determines whether the added
credit control is Pareto-beneficial.
