# LLM attention benchmark suite

- item_id: `item_eval_llm_attention_suite_v1`
- layer: `cross`
- kind: `architecture`
- status: `seed`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-04-17T00:00:00Z`
- updated_utc: `2026-04-26T00:00:00Z`
- proposal_id:
- proposal_path:

## Problem
- the current ONNX terminal-softmax benchmark inventory is still dominated by
  single-tail classifier paths such as `logistic_regression`
- that inventory is sufficient for terminal lowering bring-up and physical
  validation, but it is too weak to justify LLM-oriented scheduler or
  architecture decisions
- repeated-softmax behavior, queue pressure, overlap, and per-token latency are
  the real target, but earlier campaigns did not exercise those properties
- this means architecture work can drift toward knobs that are measurable in
  PPA but not meaningful for LLM inference

## Candidate Idea
- define an LLM-oriented benchmark ladder first, then derive architecture and
  scheduler work from what those benchmarks expose
- stage the benchmark suite in three levels:
  - `llm_smoke_v1`: one tiny attention block with explicit `QK^T -> Softmax -> V`
  - `llm_attention_tail_v1`: repeated attention-tail pattern with multiple
    softmax-bearing operations per inference path
  - `llm_practical_v1`: small realistic decoder-style subgraph with repeated
    blocks and sequence-length sensitivity

## Why It Might Matter
- puts the first optimization goal on LLM behavior rather than on isolated
  softmax or mapper microbenchmarks
- gives a principled basis for later decisions about:
  - softmax internal pipelining
  - output buffering
  - queue-depth policy
  - DMA/compute overlap
- reduces the risk of spending on architecture knobs that do not move the
  intended workload class

## Required Work
- l1 change: not required for the first benchmark-definition step
- l2 change: likely later, after benchmark evidence shows what matters
- mapper change: likely later, especially for repeated-softmax scheduling
- quality gate required: yes, once realistic attention models are added, because
  scheduler/mapper changes must preserve numerically meaningful outputs

## Benchmark Plan
- phase 1: benchmark definition
  - create `llm_smoke_v1` with one bounded attention block and fixed small
    sequence lengths
  - create `llm_attention_tail_v1` with at least 2-4 softmax-bearing operations
    per inference path so output staging and queue effects are visible
- phase 2: scheduler visibility
  - add reporting for:
    - per-token latency
    - steady-state throughput
    - queue stall cycles
    - softmax-engine occupancy
    - overlap / backpressure events
- phase 3: practical slice
  - define `llm_practical_v1` as a small decoder-style subgraph once the smoke
    and attention-tail slices are stable

## Current Scaffold
- `llm_smoke_v1` exists as a generated model set, campaign scaffold,
  deterministic numerical reference fixture set, and first candidate-output
  fixture path
- `llm_attention_tail_v1` exists as a generated model set, campaign scaffold,
  deterministic numerical reference fixture set, and first candidate-output
  fixture path
- the tail suite covers sequence lengths `32`, `64`, and `128` with 2-4
  softmax-bearing blocks per model path

## Architecture Implications
- no new architecture proposal should be launched first for “softmax pipeline
  balance” unless the benchmark suite shows that repeated-softmax workloads are
  actually sensitive to that knob
- likely first architecture follow-ons after this suite:
  - internal softmax pipeline partitioning
  - softmax output buffering
  - queue-depth-aware overlap controls

## Scheduler Implications
- the scheduler/perf model must become benchmark-driven:
  - repeated-softmax issue and retire behavior must be visible
  - softmax pipeline depth must affect modeled completion timing if it is to be
    evaluated as a scheduler knob
  - stall reasons must be reported explicitly, not only total completion time

## Evaluation Sketch
- local:
  - define the model-set manifest shape and the first two benchmark slices
  - confirm that at least one slice has multiple softmax-bearing operations
  - extend perf/scheduler reporting to expose queue and overlap behavior
- remote:
  - first run `llm_smoke_v1` as a bounded bring-up benchmark
  - then run `llm_attention_tail_v1` to decide whether scheduler and
    architecture work should proceed
  - defer broader architecture ranking until the attention-tail evidence exists

## Inputs / Sources
- `runs/models/README.md`
- `runs/models/llm_smoke_v1/manifest.json`
- `runs/models/llm_attention_tail_v1/manifest.json`
- `runs/campaigns/npu/e2e_eval_llm_smoke_v1/campaign.json`
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign.json`
- `npu/mapper/examples/gen_llm_attention_tail_suite_lite.py`
- `docs/architecture/llm_attention_benchmark_ladder.md`

## Open Questions
- what minimum remote evidence is needed before ranking softmax output buffering
  against pipeline-depth changes
- whether the first practical benchmark should include KV-style traffic or stay
  limited to attention-tail compute

## Promotion Rule
- promote when the item names:
  - the first model-set IDs to be created
  - the exact scheduler metrics to expose
  - the rule that architecture work follows benchmark evidence rather than
    preceding it
