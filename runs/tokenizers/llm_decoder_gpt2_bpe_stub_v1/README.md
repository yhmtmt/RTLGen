LLM Decoder GPT-2 BPE Stub v1
=============================

Purpose
-------
File-backed GPT-2-style BPE tokenizer bundle scaffold for the first exact
reference decoder path.

Current status
--------------
Stub bundle only.

What exists now:
- `manifest.json`
- `vocab.json`
- `merges.txt`
- explicit special-token policy
- byte-level pretokenization metadata
- normalization metadata

What does not exist yet:
- model-faithful full tokenizer assets
- pinned decoder export that consumes this tokenizer
- runtime tokenization support in the decoder backend path

This bundle exists to pin the expected asset shape for the first real decoder
reference tokenizer family before the actual model/export pair is integrated.
