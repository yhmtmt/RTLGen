# Composed Q12/PWL Softmax Datapath

- `proposal_id`: `prop_l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_v1`
- `candidate_id`: `l1_decoder_attention_dual_stream_composed_q12_pwl_softmax_ppa_v1`
- `scope`: Layer-1 PPA for a composed dual-stream attention datapath with q12/PWL reciprocal softmax.

The current composed reciprocal-LUT variant frontier selected the q8 S8/W8 softmax wrapper on latency and area, but the Llama7B-shape proxy marks that precision family as risky. This point keeps the same two int8 compute streams and q8/v6 value streams, while replacing the S8/W8 softmax with an in-wrapper q12 PWL reciprocal softmax.
