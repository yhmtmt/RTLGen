LLM Decoder Eval Tiny v1
========================

Purpose
-------
Tiny curated prompt set for the first decoder-quality gate.

This dataset is intentionally small and inference-oriented. It is not a training
set and not a benchmark for model capability. Its role is to provide a stable,
cheap acceptance slice for approximate-hardware evaluation.

Current status
--------------
Placeholder contract only.

What exists now:
- `manifest.json`
- `samples.jsonl`

What does not exist yet:
- tokenizer wiring
- decoder model binding
- saved reference next-token IDs
- continuation/perplexity metrics

Intended use
------------
- greedy next-token exact-match checks
- bounded continuation checks later
- regression gating for approximation work after the decoder model path exists
