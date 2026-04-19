# LLM attention benchmark suite

- item_id: `item_eval_llm_attention_suite_v1`
- layer: `cross`
- kind: `architecture`
- status: `seed`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-04-17T00:00:00Z`
- updated_utc: `2026-04-17T00:00:00Z`
- proposal_id:
- proposal_path:

## Problem
- the current evaluation stack can validate terminal softmax behavior, but it
  does not yet represent repeated attention-style LLM workloads well enough to
  drive scheduler or architecture choices
- current imported softmax-tail evidence is still centered on a single
  classifier-tail model, so it cannot answer whether output staging, overlap,
  or queueing matter for LLM-style inference

## Candidate Idea
- define and stage an LLM-oriented attention benchmark suite first, then derive
  scheduler and architecture work from that suite
- first benchmark ladder:
  - `llm_smoke_v1`
  - `llm_attention_tail_v1`
  - `llm_practical_v1`

## Why It Might Matter
- keeps the next architecture proposals honest about the target workload
- creates a reusable evaluation base for later work on:
  - softmax pipelining
  - buffering
  - overlap scheduling
  - queue-depth policy

## Required Work
- benchmark/model-set definition
- scheduler/perf reporting extension
- later architecture work only after benchmark evidence exists

## Evaluation Sketch
- local:
  - define the benchmark manifests and sequence-length sweep shape
  - expose scheduler metrics needed for repeated-softmax analysis
- remote:
  - run bounded `llm_smoke_v1`
  - follow with `llm_attention_tail_v1`
  - defer broader architecture ranking until those runs exist

## Promotion Rule
- promote when the benchmark ladder, metrics, and gating logic are explicit

## Concrete Benchmark Contract
- benchmark contract doc: `docs/architecture/llm_attention_benchmark_ladder.md`
- immediate benchmark target: `llm_smoke_v1`
- current state: `llm_smoke_v1` now exists as a generated model set, first campaign scaffold, deterministic numerical reference fixture set, and first candidate-output fixture path
- current boundary: this is still an attention-proxy smoke suite, not a dataset-backed decoder benchmark
- next implementation step: move from proxy candidate/reference comparison to later-stage decoder/data/training-backed accuracy evaluation for approximate hardware decisions
