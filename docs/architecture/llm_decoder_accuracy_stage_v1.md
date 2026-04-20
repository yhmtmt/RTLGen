# LLM Decoder Accuracy Stage v1

## Purpose

Define the first data-backed decoder-quality stage that should follow the
current `llm_smoke_v1` attention-proxy bring-up.

The repo now has:
- runnable attention-proxy smoke models,
- scheduler/perf counters for repeated softmax,
- deterministic numerical reference fixtures,
- a first candidate-output comparison path.

That is enough to validate proxy numerical drift, but it is not enough to make
LLM architecture decisions. The next stage must evaluate inference quality on a
small decoder-style benchmark with curated prompts and a reproducible reference
path.

## Current Boundary

What exists today:
- `runs/models/llm_smoke_v1/manifest.json`
- `runs/models/llm_smoke_v1/reference_manifest.json`
- `runs/models/llm_smoke_v1/candidate_manifest.json`
- `npu/eval/compare_llm_reference.py`
- `runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`
- `runs/datasets/llm_decoder_eval_tiny_v1/reference_manifest.json`
- `runs/tokenizers/llm_decoder_space_prefix_v1/manifest.json`
- `runs/models/llm_decoder_tiny_v1/model_contract.json`
- `npu/eval/decoder_backend.py`
- `npu/eval/gen_llm_decoder_reference_suite.py`

What does not exist yet:
- a decoder-style model set,
- tokenizer-faithful reference inference wiring,
- token-level quality metrics in campaign/report outputs,
- any dataset-backed acceptance gate for approximate hardware beyond reference-only placeholders.

## Immediate Goal

Add the smallest useful decoder-quality harness for inference-time evaluation.

This stage should answer:
- when approximate NPU outputs diverge from a reference path, does the decoder
  still produce the same next token on a bounded prompt set?
- how much token-level drift appears before a scheduler/PPA win becomes
  unacceptable?

This stage should not wait for a training loop. Training is not the next
bottleneck. The next bottleneck is a stable inference-quality gate.

## First Benchmark Slice

### `llm_decoder_eval_tiny_v1`

Scope:
- tiny curated prompt set,
- greedy next-token evaluation,
- bounded prompt length,
- bounded continuation length,
- deterministic reference outputs.

Required artifacts:
- dataset manifest:
  - `runs/datasets/llm_decoder_eval_tiny_v1/manifest.json`
- prompt samples:
  - `runs/datasets/llm_decoder_eval_tiny_v1/samples.jsonl`
- model contract README:
  - future `runs/models/llm_decoder_tiny_v1/README.md`
- evaluation campaign scaffold:
  - future `runs/campaigns/npu/e2e_eval_llm_decoder_accuracy_v1/README.md`

## Required Metrics

Stage-1 required metrics:
- next-token exact-match rate,
- top-k containment rate if logits are available,
- mean absolute error / RMSE on selected decoder tensors,
- per-token latency,
- repeated-softmax occupancy and stall counters from the existing perf path.

Stage-2 desirable metrics:
- short continuation exact-match,
- token-level negative log-likelihood,
- perplexity on a bounded held-out slice.

## Reference Path Contract

The first reference path should be Python inference, not training.

Required properties:
- fixed tokenizer version,
- fixed prompt text,
- deterministic decoding policy,
- saved reference outputs for:
  - selected intermediate tensors,
  - next-token IDs,
  - optional logits/top-k summaries.

## Architecture Decision Rule

Do not use decoder-quality language to justify architecture changes until this
stage exists.

Allowed before this stage:
- proxy numerical comparison on `llm_smoke_v1`,
- scheduler/perf conclusions about repeated-softmax behavior.

Not allowed before this stage:
- claiming an approximate softmax or pipeline change is acceptable for LLM use
  based only on proxy tensor drift.

## Concrete Next Deliverables

1. Add the tiny decoder evaluation dataset contract and seed samples.
2. Define the reference-output artifact shape for decoder inference.
3. Add one first decoder-model placeholder contract.
4. Add campaign/report fields for token-level quality metrics.
5. Only after that, wire real model execution and approximation sweeps.

## Current Scaffold Status

The repo now has the first explicit decoder-quality binding layer:
- dataset manifest bound to a tokenizer manifest and model contract,
- deterministic per-sample reference artifacts for greedy next-token checks,
- deterministic candidate-only placeholders against the same contract,
- a comparison-ready reference/candidate schema,
- an exact-match summary utility for token-level placeholder evaluation,
- an explicit backend interface that can later compare software emulation and hardware-oriented execution for equivalence.

This is still not a real decoder inference stack. It is a contract layer only.
