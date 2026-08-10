# Llama7B RMSNorm Phase-3 Bounded Nangate45 Design

This design package is the Layer-1 physical entry point for the merged
Llama7B BF16 RMSNorm Phase-3 RTL.

- `LANES=16`
- hidden size fixed at `4096`
- full ready/valid row, gamma, and output beats
- exact Phase-1 accumulation and Phase-2 reciprocal-square-root/output narrowing

Measurement limitation:

- `row_mem` and `gamma_mem` remain inferred register arrays in the generated RTL.
- This package is intentionally not SRAM-backed and must not be used as SRAM
  evidence in later architecture summaries.

