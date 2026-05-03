# Decoder Trained-Weight Tiny Quality Gate

- `proposal_id`: `prop_l2_decoder_trained_tiny_quality_v1`
- `item_id`: `l2_decoder_trained_tiny_quality_v1`
- abstraction: `decoder_trained_tiny_quality`

The previous decoder approximation work used a tiny ONNX decoder harness to
prove equivalence plumbing and then swept q8, q12, bf16, and PWL normalization
choices. The latest frontier candidate is bf16 reciprocal PWL with logit score
tie-break recovery, but the current evidence is still tied to a tiny random
model and proxy prompt distributions.

This job adds the first trained-weight smoke. It imports a small trained
GPT-2-family checkpoint into the existing decoder contract shape and runs the
same reference, candidate, compare, sweep, and recovery-summary path. The goal
is to detect whether trained logit margins immediately break the recovered
bf16/PWL row before spending evaluator time on larger checkpoints.

Expected output:

- `decoder_quality_sweep__l2_decoder_trained_tiny_quality_v1.json`
- `decoder_trained_tiny_quality__l2_decoder_trained_tiny_quality_v1.json`
- `decoder_trained_tiny_quality__l2_decoder_trained_tiny_quality_v1.md`

Passing this gate only authorizes the next larger trained-model check. It does
not prove distribution robustness across larger LLMs or larger hardware arrays.
