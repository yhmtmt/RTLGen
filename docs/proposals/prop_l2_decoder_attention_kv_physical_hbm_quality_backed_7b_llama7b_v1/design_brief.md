# Design Brief

The existing quality-backed HBM frontier uses TinyLlama native quality evidence
as the precision gate. The active `l2_decoder_attention_kv_model_native_quality_7b_v1`
job will provide a larger-checkpoint gate. This proposal prepares the L2 rerank
that consumes that artifact while preserving the conservative native-GQA KV16/KV8
frontier until KV4 is explicitly reviewed.
