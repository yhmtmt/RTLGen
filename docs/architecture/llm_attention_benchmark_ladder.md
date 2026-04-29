# LLM Attention Benchmark Ladder

## Purpose

Define the benchmark-first contract for LLM-oriented Layer 2 work.

This document exists to prevent the next softmax/scheduler proposals from being
validated against the wrong workload. Current Layer 2 evidence is still centered
on terminal-softmax classifier tails. That is useful for bring-up, but it is
not sufficient to justify LLM-facing scheduler or buffering choices.

## Current Boundary

The current repo now supports the narrow attention-proxy path needed for
`llm_smoke_v1`: repeated `Gemm -> Softmax -> Gemm` blocks lower through the
mapper and run through the perf/report flow.

That means:
- `llm_smoke_v1` is now a runnable `runs/models/<id>/manifest.json` campaign input,
- deterministic numerical reference fixtures exist for the same model binaries,
- a first candidate-output path also exists with current int8 placeholder semantics,
- `llm_attention_tail_v1` now stages the next repeated-tail slice with sequence
  lengths `32`, `64`, and `128` and 2-4 softmax-bearing blocks per model path,
- but this is still only a smoke-stage proxy suite, not a full decoder-quality
  benchmark with dataset/training-backed accuracy evaluation.

So the immediate deliverable after bring-up is no longer just the reference path.
The repo now supports reference-vs-candidate numerical comparison for the smoke
suite. The next accuracy step is richer decoder benchmarks and true LLM accuracy gating.

## Benchmark Ladder

### `llm_smoke_v1`

Goal:
- prove that the evaluation stack can represent one tiny attention block with a
  non-terminal `Softmax` in the middle of the graph
- establish the first real LLM-oriented scheduler counters

Required graph families:
1. `attn1_s32_h64`
- one attention block
- sequence length `32`
- hidden width `64`
- shape intent: small enough for local bring-up, but still includes repeated
  matrix products around a non-terminal `Softmax`

2. `attn1_s64_h64`
- one attention block
- sequence length `64`
- same hidden width so sequence pressure can be isolated

3. `attn2_s32_h64`
- two repeated attention blocks
- used to prove that repeated softmax-bearing work exists in one inference path

Required operator structure:
- `MatMul(Q, K^T)` or equivalent linear proxy
- `Softmax` on the score tensor
- `MatMul(P, V)` or equivalent linear proxy
- optional residual/output projection only if needed to keep shapes explicit

Success criteria:
- the mapper accepts the graph without rewriting away the non-terminal softmax
- the perf trace distinguishes score generation, softmax service, and value
  projection work clearly enough to attribute stalls
- at least two softmax-bearing episodes exist in one model path across the set

### `llm_attention_tail_v1`

Goal:
- move from smoke validation to a shape that is actually useful for scheduler
  comparison

Required expansion:
- sequence sweep: `32`, `64`, `128`
- repeated attention blocks: `2` to `4`
- at least one model where multiple softmax episodes are visible in a single
  token path

Metrics that must be present before running this suite:
- per-token latency
- steady-state throughput
- softmax-engine occupancy
- queue stall cycles by cause
- overlap/backpressure events

Accuracy requirement after smoke bring-up:
- later revisions must compare approximate-hardware outputs against a reference path
- final architecture decisions must include accuracy/precision loss, not only schedule or PPA gains

### `llm_attention_tail_stress_v1`

Goal:
- test whether the low softmax occupancy and zero wait/backpressure evidence
  from `llm_attention_tail_v1` was a benchmark-size artifact

Required expansion:
- sequence sweep: `128`, `256`
- repeated attention blocks: `4` to `6`
- enough repeated non-terminal `Softmax` episodes to make a scheduler or
  buffering bottleneck visible if the current tail proxy was under-stressed

Decision use:
- if softmax occupancy, dependency wait, or backpressure remains low, continue
  toward richer decoder-style benchmarks before proposing a softmax datapath
  change
- if any of those counters becomes material, use this campaign to choose the
  next focused architecture proposal: softmax buffering, pipeline partitioning,
  or scheduler overlap policy

### `llm_practical_v1`

Goal:
- small but realistic decoder-style proxy for actual architecture decisions

Required characteristics:
- repeated blocks
- KV-like storage pressure or an explicit proxy for it
- enough work to expose overlap limits, not only single-op latency

Initial proxy shape:
- active-token batches: `16`, `32`
- KV-context score dimensions: `256`, `512`
- repeated attention blocks: `4` to `6`
- graph form remains runnable through the current ONNX-lite mapper path:
  `Gemm(score) -> Softmax -> Gemm(value)`, with `score_dim` representing the
  KV-context window

## Inverted Planning Rule

Architecture and scheduler changes must be derived from this ladder, not the
other way around.

Order of work:
1. benchmark contract
2. mapper enablement for non-terminal softmax attention graphs
3. perf/scheduler counters for repeated-softmax analysis
4. only then proposal work on:
   - softmax internal pipelining
   - output buffering
   - queue-depth policy
   - overlap scheduling

## Concrete Next Deliverables

### Mapper/graph enablement
- add a tiny ONNX-lite attention generator for `llm_smoke_v1`
- extend mapper lowering beyond terminal softmax-only handling
- preserve shape provenance so score/probability/value stages remain visible

### Scheduler/perf reporting
- report softmax issue count and completion count
- report softmax busy cycles
- report queue stalls split by:
  - softmax busy
  - DMA busy
  - GEMM busy
  - dependency wait
- report per-model token-equivalent latency summary

### Campaign artifacts to create after enablement
- `runs/models/llm_smoke_v1/manifest.json`
- `runs/models/llm_smoke_v1/README.md`
- `runs/campaigns/npu/e2e_eval_llm_smoke_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_llm_smoke_v1/README.md`
- `runs/models/llm_attention_tail_v1/manifest.json`
- `runs/models/llm_attention_tail_v1/README.md`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/README.md`
- `runs/models/llm_attention_tail_stress_v1/manifest.json`
- `runs/models/llm_attention_tail_stress_v1/README.md`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/README.md`
- `runs/models/llm_practical_v1/manifest.json`
- `runs/models/llm_practical_v1/README.md`
- `runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_llm_practical_v1/README.md`

## Decision Rule

Do not launch `item_l2_softmax_macro_pipeline_balance_v1` as a real proposal
until `llm_attention_tail_v1` has validated repeated-tail evidence and the
scheduler can measure the softmax-related counters listed above.

If `llm_attention_tail_v1` reports low pressure, run
`llm_attention_tail_stress_v1` before proposing new softmax datapath work.

If the stress ladder still reports low pressure, run `llm_practical_v1` to add
KV-context proxy pressure before opening a datapath proposal.
