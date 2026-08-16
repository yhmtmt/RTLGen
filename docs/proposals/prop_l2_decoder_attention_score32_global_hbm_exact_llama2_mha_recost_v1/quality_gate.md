# Quality Gate

- Require the merged finite-endpoint composed recost and its explicit GQA8 contract.
- Require the exact-reduction source, deterministic HBM replay, and calibrated HBM energy inputs.
- Replay all active-cluster bytes through one global HBM controller per wave.
- Recompute QKV projection, KV writes/cache, residency fraction, HBM latency, and HBM energy for 32-head MHA.
- Keep reduction payload and fixed shared-SRAM bytes invariant across GQA8 and MHA.
- Rerun workload-complete finite endpoint scheduling after HBM changes wave cadence.
- Record exact structural identity separately from arithmetic quality.
- Do not promote either score32 row without native Llama-2-7B generation-quality evidence.
- Keep HBM RTL/vendor signoff and workload clock-gating power explicit.
