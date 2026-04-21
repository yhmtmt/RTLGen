LLM Decoder GPT-2 BPE Stub v1
=============================

Purpose
-------
File-backed GPT-2-style BPE tokenizer bundle for the first exact-reference
decoder path.

Current status
--------------
Fetched exact-reference asset bundle.

What exists now:
- `manifest.json`
- `vocab.json`
- `merges.txt`
- `tokenizer.json`
- `tokenizer_config.json`
- `special_tokens_map.json`
- explicit special-token policy
- byte-level pretokenization metadata
- normalization metadata

What does not exist yet:
- a renamed non-`stub` bundle id
- a larger-model tokenizer pair beyond this first tiny decoder seed

This bundle now contains the real GPT-2-family tokenizer assets fetched from `onnx-community/tiny-random-gpt2-ONNX` and validated against the local ONNX exact-reference runner. The historical `*_stub_v1` id is retained for compatibility with the earlier scaffolded manifests.
