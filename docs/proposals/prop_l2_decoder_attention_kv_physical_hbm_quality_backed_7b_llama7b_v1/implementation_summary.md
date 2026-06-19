# Implementation Summary

- Add `decoder_attention_kv_physical_hbm_quality_backed_7b` to the L2 task
  generator.
- Reuse the physical-HBM estimator with `gqa8` and `kv_bits=16,8`.
- Attach the 7B native quality artifact path to the decoder contract.
- Do not run OpenROAD/PPA for this L2 rerank.
