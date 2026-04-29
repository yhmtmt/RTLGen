# Design Brief

## Proposal
- `proposal_id`: `prop_l2_llm_attention_tail_stress_ladder_v1`
- `title`: `LLM attention-tail stress ladder`

## Problem
`llm_attention_tail_v1` produced useful scheduler visibility, but its current
evidence showed low softmax occupancy and no dependency-wait or backpressure
pressure. Before proposing a new softmax datapath, the benchmark ladder needs a
bounded stress step that can distinguish insufficient workload pressure from a
real absence of a softmax bottleneck.

## Hypothesis
Increasing sequence length and repeated softmax-bearing blocks will expose
softmax occupancy, wait cycles, or backpressure if the previous tail suite was
too small. If those counters remain low, architecture work should move toward a
richer decoder-style benchmark before softmax-specific datapath changes.

## Evaluation Scope
- direct comparison set:
  - `llm_attention_tail_stress_v1` campaign on `nangate45`
  - `fp16_nm1` and `fp16_nm2`
  - `flat_nomacro` and `hier_macro`
  - three stress-tail models, three samples per point
- evaluation mode:
  - `broad_ranking`
- expected result:
  - collect pressure evidence, not prove a paired baseline win/loss hypothesis
- excluded first-stage comparisons:
  - new softmax hardware changes
  - mapper rewrites
  - full decoder-quality or KV-cache behavior

## Knowledge Inputs
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_stress_v1/campaign.json`
- `runs/models/llm_attention_tail_stress_v1/manifest.json`
- `docs/architecture/llm_attention_benchmark_ladder.md`
- `docs/proposals/prop_l2_llm_attention_tail_scheduler_visibility_v1/proposal.json`

## Candidate Direction
No RTL or mapper candidate is promoted by this proposal. The result should pick
the next branch: softmax buffering, softmax pipeline partitioning, scheduler
overlap policy, or richer decoder-style benchmarking.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- note: measurement-only stress step approved after the initial scheduler
  visibility run reported no material softmax pressure.
