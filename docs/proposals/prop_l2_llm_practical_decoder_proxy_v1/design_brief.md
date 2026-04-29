# Design Brief

## Proposal
- `proposal_id`: `prop_l2_llm_practical_decoder_proxy_v1`
- `title`: `LLM practical decoder proxy`

## Problem
The attention-tail stress ladder increased sequence length and repeated
softmax episodes, but still reported low softmax occupancy and zero dependency
wait or backpressure. Before opening softmax datapath work, the benchmark
ladder needs a practical decoder-style proxy that introduces KV-context
pressure while remaining runnable in the current campaign stack.

## Hypothesis
Active-token batches attending over larger KV-context score dimensions will
expose scheduler, softmax, or memory-overlap pressure if tail-only graphs were
still too narrow. If pressure remains low, the next step should be true
dataset-backed decoder execution rather than another graph-proxy stress point.

## Evaluation Scope
- direct comparison set:
  - `llm_practical_v1` campaign on `nangate45`
  - `fp16_nm1` and `fp16_nm2`
  - `flat_nomacro` and `hier_macro`
  - three practical decoder-style proxy models, three samples per point
- evaluation mode:
  - `broad_ranking`
- expected result:
  - collect scheduler/PPA pressure evidence, not prove a paired baseline
    win/loss hypothesis
- excluded first-stage comparisons:
  - softmax hardware changes
  - mapper rewrites
  - dataset-backed quality claims

## Knowledge Inputs
- `runs/campaigns/npu/e2e_eval_llm_practical_v1/campaign.json`
- `runs/models/llm_practical_v1/manifest.json`
- `docs/architecture/llm_attention_benchmark_ladder.md`
- `docs/architecture/llm_decoder_accuracy_stage_v1.md`

## Candidate Direction
No RTL or mapper candidate is promoted by this proposal. The result should pick
the next branch: scheduler/KV-context modeling, dataset-backed decoder
execution, or a focused architecture proposal only if pressure is material.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- note: measurement-only practical proxy approved after the attention-tail
  stress ladder reported no material softmax pressure.
