# Llama-7B BF16 RMSNorm l16 Wrapper

This wrapper is the bounded Layer 1 physical entry point for the Phase 3
Llama-7B RMSNorm service.

It fixes the hidden row at `4096` BF16 elements, uses `LANES=16`, implements the
Phase 1 exact 48-bit block-floating accumulation and the Phase 2 frozen
reciprocal-square-root/output narrowing arithmetic, and exposes the full
ready/valid streaming interface with canonical protocol-error replay.

The generator is `npu/rtlgen/gen_llama7b_rmsnorm.py`. The checked config below
is intended for future OpenROAD wrapper generation and PPA collection.
