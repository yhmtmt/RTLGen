# Evaluation Gate

Dispatch only after:

- `l2_decoder_attention_kv_model_native_quality_7b_v1` has materialized the
  7B native quality JSON/Markdown artifacts.
- `l2_decoder_attention_kv_physical_hbm_quality_backed_llama7b_v1` remains
  available as the TinyLlama-quality-backed baseline.

The job is Layer 2 only and must not run OpenROAD/PPA.
