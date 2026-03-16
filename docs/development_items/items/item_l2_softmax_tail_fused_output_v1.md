# Softmax-tail fused output path

- item_id: `item_l2_softmax_tail_fused_output_v1`
- layer: `layer2`
- kind: `architecture`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-16T05:20:00Z`
- updated_utc: `2026-03-16T05:20:00Z`
- proposal_id: `prop_l2_softmax_tile_fusion_v1`
- proposal_path: `docs/developer_loop/prop_l2_softmax_tile_fusion_v1`

## Problem
- the accepted softmax-tail integrated path still pays a terminal `dma_y`
  routing hop after dedicated `SOFTMAX`
- the workload is small enough that descriptor-tail overhead can matter

## Candidate Idea
- allow the architecture to route terminal `SOFTMAX` directly to `Y_DRAM`
- keep the compute path unchanged and remove only the terminal copy hop

## Why It Might Matter
- may reduce terminal latency overhead on softmax-tail classifiers
- may improve the practical value of the dedicated softmax path without a
  broader shell redesign

## Required Work
- l1 change: no new Layer 1 block required beyond the current softmax seed
- l2 change: yes
- mapper change: yes
- quality gate required: yes

## Evaluation Sketch
- local:
  - mapper regression
  - routing-equivalence quality precheck
- remote:
  - bounded Layer 2 campaign on the imported softmax-tail model family

## Inputs / Sources
- current integrated softmax-tail campaign baselines
- imported softmax-tail model family
- developer discussion about numerical-quality gates

## Open Questions
- is the latency gain meaningful enough to justify a new architecture point?
- does the benefit hold beyond the tiny softmax-tail classifier?

## Promotion Rule
- promote when direction gate approves a bounded softmax-tail fused-output
  experiment with explicit mapper scope and a quality precheck plan
