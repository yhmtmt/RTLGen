# Decoder bf16/PWL Scale-Proxy Recovery Probe

- `proposal_id`: `prop_l2_decoder_bf16_pwl_scale_probe_v1`
- `item_id`: `l2_decoder_bf16_pwl_scale_probe_v1`
- abstraction: `decoder_bf16_pwl_scale_probe`

The current bf16/PWL plus logit tie-break recovery is exact-safe on the broad-v2
tiny decoder setup, but that result can fail to generalize as model outputs and
ranking pressure grow. This job adds a rough scale-proxy screen before claiming
that the recovery is the next architectural frontier.

The screen keeps the same tiny ONNX model so it remains cheap, but changes the
stress axes:

- top-k increases from 5 to 16 while still ranking over the full 50k-token vocab
- prompt regimes add longer context, denser code/symbolic text, repetition,
  low-margin continuations, and instruction/dialogue cases
- q12 exact-normalization and q8 reciprocal rows remain as controls beside the
  bf16/PWL baseline and bf16/PWL logit tie-break recovery

Expected output:

- `decoder_quality_sweep__l2_decoder_bf16_pwl_scale_probe_v1.json`
- `decoder_bf16_pwl_scale_probe__l2_decoder_bf16_pwl_scale_probe_v1.json`
- `decoder_bf16_pwl_scale_probe__l2_decoder_bf16_pwl_scale_probe_v1.md`

This is not evidence from a larger trained LLM. It is a cheap guard against a
false conclusion from one small benchmark setup, and it decides whether the next
step should be larger-model import or integrated datapath PPA.
