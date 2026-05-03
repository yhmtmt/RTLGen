# LLM Decoder Tiny GPT-2 Trained v1

This model binding is the first trained-weight smoke point for the decoder
quality harness. It uses `sshleifer/tiny-gpt2` exported to ONNX with the same
`command_json_v1` GPT-2 decoder interface used by `llm_decoder_tiny_v1`.

Scope:
- real GPT-2-family tokenizer assets
- trained checkpoint weights rather than random ONNX weights
- ONNX Runtime exact-reference execution
- post-logit candidate probability-path emulation

Limits:
- this checkpoint is intentionally tiny, so it is not evidence for larger model
  hidden-size, layer-count, or useful language quality
- it is a gate before larger `distilgpt2` or GPT-2-class coverage, not a final
  architecture decision point
