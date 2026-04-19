# LLM decoder accuracy stage

- item_id: `item_eval_llm_decoder_accuracy_stage_v1`
- layer: `cross`
- kind: `architecture`
- status: `seed`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-04-19T00:00:00Z`
- updated_utc: `2026-04-19T00:00:00Z`
- proposal_id:
- proposal_path:

## Problem
- the current repo can compare proxy attention outputs against deterministic
  references, but it still cannot answer whether an approximate path preserves
  decoder behavior on text prompts
- there is still no dataset-backed decoder-quality gate, no tokenizer/reference
  inference contract, and no token-level acceptance metric

## Candidate Idea
- add the first bounded decoder-quality stage for inference evaluation
- keep the first stage small and curated:
  - tiny prompt set,
  - greedy next-token target,
  - deterministic reference outputs,
  - token-level exact-match metrics
- defer training-loop work until after inference-quality gating exists

## Why It Might Matter
- creates the first practical architecture gate beyond proxy tensor drift
- keeps approximate-hardware work tied to actual decoder behavior
- gives later LLM practical benchmarks a stable evaluation contract

## Required Work
- dataset contract under `runs/datasets/llm_decoder_eval_tiny_v1/`
- reference-output schema for decoder inference
- campaign/report extensions for token-level quality metrics
- later decoder-model and tokenizer wiring

## Evaluation Sketch
- local:
  - stage the dataset contract and prompt samples
  - define the metric schema and reference-output schema
- remote:
  - run the first decoder-quality campaign once a real decoder model is wired

## Concrete Benchmark Contract
- benchmark contract doc: `docs/architecture/llm_decoder_accuracy_stage_v1.md`
- immediate dataset target: `llm_decoder_eval_tiny_v1`
- current state: only proxy attention comparison exists; decoder-quality gating does not
- next implementation step: wire a tiny decoder prompt/reference path and token-level metrics
