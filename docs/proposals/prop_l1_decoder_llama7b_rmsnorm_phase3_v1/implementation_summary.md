# Llama-7B RMSNorm Phase 3 Implementation Summary

- Added `npu/rtlgen/gen_llama7b_rmsnorm.py` as a bounded RTL generator for the
  `4096`-element BF16 RMSNorm service using `LANES=16`.
- The generated RTL keeps the Phase 1 exact 48-bit block-floating accumulation,
  freezes the Phase 2 Q2.24 variance normalization, checked 192x21 seed ROM,
  one-iteration Newton update with `+4` Q1.20 bias, and single-boundary BF16
  output narrowing.
- The service exposes row/gamma input beats and output beats through ready/valid
  handshakes and canonicalizes exponent-255 or framing errors into full-row
  `0x7fc0` replay with sticky transaction error status.
- Added deterministic RTL tests in `tests/test_llama7b_rmsnorm_phase3.py`:
  direct generator bootstrap, Verilator lint, Yosys synth check, random finite
  oracle comparison under output backpressure, framing-error canonicalization,
  and exponent-255 canonicalization.
- Added `npu/rtlgen/examples/llama7b_rmsnorm_bf16_l16.json` and the PPA wrapper
  config package at
  `runs/designs/activations/llama7b_rmsnorm_bf16_l16_wrapper/`.

Remaining abstraction is limited to physical implementation choices around the
internal row/gamma storage arrays and any later memory-macro replacement or
clock-gating refinement; the arithmetic and streaming contract are now emitted as
real RTL and checked against the Python Phase 2 oracle.
