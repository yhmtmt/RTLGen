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
Bound reference-placeholder contract.

What exists now:
- `manifest.json`
- `samples.jsonl`
- `reference_manifest.json`
- `candidate_manifest.json`
- deterministic tokenizer/model binding for reference-only artifacts

What does not exist yet:
- real tokenizer wiring
- real decoder model binding
- continuation/perplexity metrics

Intended use
------------
- greedy next-token exact-match checks
- bounded continuation checks later
- regression gating for approximation work after the decoder model path exists

Current binding
---------------
- tokenizer: `runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json`
- model contract: `runs/models/llm_decoder_tiny_v1/model_contract.json`

These are scaffolding artifacts, not a real decoder deployment path.

Comparison
----------
- reference vs candidate summary: `python3 npu/eval/compare_llm_decoder_quality.py --reference-manifest runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json --candidate-manifest runs/datasets/llm_decoder_eval_tiny_v1/candidate_manifest.json`
