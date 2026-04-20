LLM Decoder WordPiece Stub v1
=============================

Purpose
-------
File-backed tokenizer bundle contract for the first real decoder-tokenizer path.

Current status
--------------
Stub bundle only.

What exists now:
- `manifest.json`
- `vocab.json`
- explicit special-token mapping
- a loader path in `npu/eval/llm_decoder_quality.py`

What does not exist yet:
- model-faithful normalization rules
- merge rules or tokenizer model files
- a pinned decoder export that actually consumes this tokenizer

This bundle exists to move the repo from a placeholder split rule toward a real
file-backed tokenizer contract without pretending that the final tokenizer
assets are already pinned.
