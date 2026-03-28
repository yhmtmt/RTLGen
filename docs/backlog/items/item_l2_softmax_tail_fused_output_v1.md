# Softmax-tail fused output path

- item_id: `item_l2_softmax_tail_fused_output_v1`
- layer: `layer2`
- kind: `architecture`
- status: `superseded`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-16T05:20:00Z`
- updated_utc: `2026-03-28T00:00:00Z`
- proposal_id: `prop_l2_softmax_tile_fusion_v1`
- proposal_path: `docs/proposals/prop_l2_softmax_tile_fusion_v1`

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
  - first-stage: compare `{non-fused, fused}` on the fixed
    `fp16_nm1_softmax_r4` baseline only
  - follow-on broad sweep only if the nm1 fusion effect is positive or still
    ambiguous after the focused proof

## Focused Comparison Set
- direct comparison:
  - current `fp16_nm1_softmax_r4` softmax baseline
  - fused-output candidate on the same `fp16_nm1_softmax_r4` hardware
- intentionally excluded from first-stage evaluation:
  - `fp16_nm2_softmax_r4`
  - broad architecture ranking across multiple module-count points
- follow-on only after a positive or ambiguous focused result:
  - reintroduce `nm2` to study whether the fusion effect changes the broader
    architecture frontier

## Inputs / Sources
- current integrated softmax-tail campaign baselines
- imported softmax-tail model family
- developer discussion about numerical-quality gates

## Open Questions
- is the latency gain meaningful enough to justify a new architecture point?
- does the benefit hold beyond the tiny softmax-tail classifier?
- should a successful nm1 fusion result be followed by a broader nm1/nm2 sweep,
  or by a separate mapper-specific proposal first?

## Promotion Rule
- promote when direction gate approves a bounded softmax-tail fused-output
  experiment with explicit mapper scope and a quality precheck plan

## Closeout
- superseded by the later overlap-probe and bounded terminal direct-output
  proposal family
- retained only as historical evidence for the first focused fused-output check
