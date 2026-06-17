# Quality Gate

- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_v1`
- `candidate_id`: `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`

This job is a physical-cost measurement for a safer softmax datapath, not final Llama7B perplexity evidence. Promotion beyond PPA still requires a follow-on quality gate that compares the q12/PWL composed softmax behavior against the accepted mixed-precision proxy or a model-native checkpoint run.
