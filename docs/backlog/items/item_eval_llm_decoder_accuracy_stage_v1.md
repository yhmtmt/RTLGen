# LLM decoder accuracy stage

- item_id: `item_eval_llm_decoder_accuracy_stage_v1`
- layer: `cross`
- kind: `architecture`
- status: `merged`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-04-19T00:00:00Z`
- updated_utc: `2026-04-28T00:00:00Z`
- proposal_id:
- proposal_path:

## Problem
- the repo can now compare proxy attention outputs against deterministic
  references, but that still does not answer whether an approximate NPU path is
  acceptable for a decoder workload
- there is no data-backed decoder prompt set, no tokenizer/reference contract,
  and no token-level quality gate
- this means the current evaluation stack can quantify tensor drift, but not
  decoder correctness or practical quality loss

## Candidate Idea
- add the first tiny decoder-quality stage for inference evaluation
- start with a bounded prompt set and greedy next-token checks before any
  broader continuation or perplexity work
- keep the first stage explicitly inference-only; a training loop is not yet
  required for architecture gating

## Why It Might Matter
- creates the first real acceptance gate for approximate hardware on an LLM-like
  workload
- prevents architecture decisions from relying only on proxy tensor error or
  scheduler/PPA improvements
- gives the later decoder benchmark stages a stable artifact contract

## Required Work
- add a curated prompt dataset contract under `runs/datasets/`
- define the reference inference artifact shape
- add token-level quality metrics to the evaluation/report path
- later add model execution and approximation sweeps against that contract

## Implementation Result
- `runs/datasets/llm_decoder_eval_tiny_v1/` now carries the bounded prompt
  slice, reference manifest, candidate manifest, and frozen per-sample
  artifacts.
- `npu/eval/llm_decoder_contract.schema.json` records the prompt,
  manifest, reference, candidate, tensor-trace, and metrics contract.
- `npu/eval/validate_llm_decoder_contract.py` validates the checked-in
  dataset linkage, SHA256s, artifact shapes, and token-level metrics.
- `npu/eval/compare_llm_decoder_quality.py` reports next-token exact-match
  and candidate top-k containment rates, plus selected tensor-trace drift.

## Evaluation Sketch
- local:
  - create the tiny prompt set and dataset manifest
  - define the reference-output schema and metric schema
- remote:
  - run the first bounded decoder-quality slice after a real decoder-model path
    exists

## Inputs / Sources
- `docs/architecture/llm_attention_benchmark_ladder.md`
- `docs/architecture/llm_decoder_accuracy_stage_v1.md`
- `runs/models/llm_smoke_v1/README.md`
- discussion on 2026-04-19 about moving from proxy tensor comparison to
  decoder-quality gating

## Promotion Rule
- promote when the dataset contract, reference-output shape, and token-level
  metrics are explicit enough to support a real decoder evaluation campaign
