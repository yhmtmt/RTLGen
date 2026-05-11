# Quality Gate

- The estimator must run without generated model artifacts.
- The committed JSON output must include inputs, assumptions, compact sweep rows, and a focus summary.
- Full per-substage sweep detail must not be committed by default; it may only be written through an explicit optional detail path.
- The markdown report must expose dominant attention substage, KV byte share, KV-limited cycle share, and effective KV bandwidth.
- The control-plane generated task must carry `decoder_attention_kv_memory` abstraction metadata and expected output paths.
- Unit tests must cover both the estimator and L2 generator hook.
