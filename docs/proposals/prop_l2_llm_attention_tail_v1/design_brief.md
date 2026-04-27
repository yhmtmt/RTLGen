# Design Brief

## Proposal
- `proposal_id`: `prop_l2_llm_attention_tail_v1`
- `title`: `LLM attention tail measurement gate`

## Problem
The merged LLM attention-tail benchmark adds softmax-tail workloads, but the
current architecture ladder needs concrete scheduler, latency, energy, and
backpressure evidence before selecting a softmax datapath or mapper follow-up.

## Hypothesis
Running the benchmark across the existing `fp16_nm1` and `fp16_nm2` architecture
points will expose whether the next useful proposal should target softmax
occupancy, scheduler stalls, memory overlap, or a different architecture
dimension.

## Evaluation Scope
- direct comparison set:
  - `llm_attention_tail_v1` campaign on `nangate45`
  - `fp16_nm1` and `fp16_nm2`
  - `flat_nomacro` and `hier_macro`
  - five attention-tail models, three samples per point
- evaluation mode:
  - `broad_ranking`
- expected result:
  - collect evidence, not prove a paired win/loss hypothesis
- excluded first-stage comparisons:
  - new softmax hardware changes
  - mapper rewrites
  - promotion of any candidate architecture before this measurement is reviewed

## Knowledge Inputs
- `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1/campaign.json`
- `docs/llm_architecture_ladder.md`
- `npu/mapper/README.md`

## Candidate Direction
No RTL or mapper candidate is promoted by this proposal. The direction is to use
the measurement result to choose the next focused LLM/softmax proposal.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-04-26T12:22:35Z
- note: measurement-only gate approved to collect attention-tail evidence after
  the benchmark suite merged.
