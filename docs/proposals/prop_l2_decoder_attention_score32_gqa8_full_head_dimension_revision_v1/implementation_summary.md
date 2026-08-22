# Implementation Summary

- Expanded deterministic query/key generation from one product to all 128
  Llama7B head dimensions per token block.
- Added explicit final-dimension sidecars and full-dot-product software
  references across direct, compositional, and fine-compositional probes.
- Moved large generated stimuli to `readmemh` sidecars to keep testbench source
  bounded while preserving exact values.
- Tightened reports and task acceptance to require explicit 128D contracts and
  corrected producer handshake counts.
- Added revision and rerank tasks that reject the legacy one-dimensional
  evidence rather than silently overwriting it.
