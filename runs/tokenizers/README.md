Runs Tokenizers
===============

Purpose
-------
Deterministic tokenizer contracts used by dataset-backed decoder-quality
evaluation.

Contract
--------
Each tokenizer lives under `runs/tokenizers/<tokenizer_id>/` and should provide:
- `manifest.json`
- optional assets such as `vocab.json`
- explicit special-token metadata when the tokenizer is intended to represent a
  real model bundle

These tokenizer contracts are separate from ONNX model-set manifests because
the first decoder-quality stage is not yet a runnable mapper/physical campaign.
It is an inference-quality scaffolding layer.

Current sets
------------
- `llm_decoder_space_prefix_v1`: placeholder leading-space word tokenizer for
  `llm_decoder_eval_tiny_v1`. This is not model-faithful tokenizer behavior; it
  exists only to make the first greedy next-token gate explicit and
  deterministic.
- `llm_decoder_wordpiece_stub_v1`: file-backed tokenizer bundle scaffold with
  explicit special-token metadata. This is the first contract shape intended
  for a pinned real decoder tokenizer, even though the current assets are still
  stubbed.
