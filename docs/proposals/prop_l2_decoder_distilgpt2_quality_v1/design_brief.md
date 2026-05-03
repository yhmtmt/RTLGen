# Decoder distilgpt2 Quality Gate

- `proposal_id`: `prop_l2_decoder_distilgpt2_quality_v1`
- `item_id`: `l2_decoder_distilgpt2_quality_v1`
- abstraction: `decoder_distilgpt2_quality`

The trained tiny GPT-2-family gate showed that the bf16/PWL path with logit
tie-break recovery can stay exact-safe on a real, but very small, trained
checkpoint. The next uncertainty is whether that behavior holds when the model
has a larger vocabulary distribution, hidden size, and layer stack.

This job materializes `distilgpt2` locally in the evaluator workspace, writes
the decoder model/tokenizer contracts, then runs the existing reference,
candidate, compare, bf16/PWL scale-probe sweep, and recovery-summary path. The
ONNX model and tokenizer assets are generated at runtime and ignored by git.

Expected output:

- `decoder_quality_sweep__l2_decoder_distilgpt2_quality_v1.json`
- `decoder_distilgpt2_quality__l2_decoder_distilgpt2_quality_v1.json`
- `decoder_distilgpt2_quality__l2_decoder_distilgpt2_quality_v1.md`

A pass strengthens the immediate frontier claim for trained GPT-2-family
decoders. It still does not prove behavior on larger LLMs, larger arrays, or
post-training recovery.
