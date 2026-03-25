# NPU nm1 hard-sigmoid vec enable

- item_id: `item_l1_npu_nm1_hardsigmoid_vec_enable_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-25T03:30:00Z`
- updated_utc: `2026-03-25T03:30:00Z`
- proposal_id: `prop_l1_npu_nm1_hardsigmoid_vec_enable_v1`
- proposal_path: `docs/developer_loop/prop_l1_npu_nm1_hardsigmoid_vec_enable_v1`
- triggered_by_proposal: `prop_l1_terminal_hardsigmoid_block_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l1_terminal_hardsigmoid_block_v1/analysis_report.md`
  - `docs/developer_loop/prop_l1_terminal_hardsigmoid_block_v1/promotion_result.json`
  - `docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1/promotion_result.json`

## Problem
- the standalone terminal hard-sigmoid wrapper now has accepted physical metrics, but
  any later hard-sigmoid mapper or terminal-output evaluation still requires an
  integrated hard-sigmoid-enabled `nm1` source rather than a standalone activation wrapper
- current `npu_fp16_cpp_nm1_cmp` still exposes only vec ops `add/mul/relu`

## Candidate Idea
- integrate bounded int8 hard-sigmoid support into the fixed `nm1` vec path
- generate a hard-sigmoid-enabled `nm1` design/config variant
- run Layer 1 physical characterization for an integrated architecture-block
  proof target before any later Layer 2 hard-sigmoid campaign is queued

## Why It Might Matter
- creates the correct physical source for later hard-sigmoid Layer 2 perf campaigns
- prevents invalid higher-layer evaluation grounded on sigmoid/tanh-only or relu-only hardware
- reuses the already-accepted reduced-proxy strategy instead of starting from a full-top run

## Required Work
- l1 change: yes
- l2 change: not in this proposal
- mapper change: not in this proposal
- quality gate required: no separate model-quality gate at this stage; output quality belongs to later Layer 2 use of the block

## Evaluation Sketch
- local:
  - integrate bounded `int8` hard-sigmoid into the `nm1` vec path
  - add legality / smoke checks
- remote:
  - first-stage integrated Layer 1 `architecture_block` reduced-proxy physical sweep
- follow-on:
  - use the accepted integrated source to seed bounded Layer 2 hard-sigmoid direct-output work

## Inputs / Sources
- `docs/developer_loop/prop_l1_terminal_hardsigmoid_block_v1/analysis_report.md`
- `docs/developer_loop/prop_l1_terminal_hardsigmoid_block_v1/promotion_result.json`
- `docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1/promotion_result.json`
- `docs/developer_loop/prop_l1_npu_nm1_tanh_vec_enable_v1/promotion_result.json`
- discussion on 2026-03-25 about stepping from standalone hard-sigmoid grounding to an integrated `nm1` source before any Layer 2 hard-sigmoid campaign

## Open Questions
- whether the sigmoid reduced-proxy pattern is sufficient for hard-sigmoid without extra hierarchy constraints
- whether a legality checkpoint should be accepted before the first reduced physical source
- whether later Layer 2 hard-sigmoid work should be standalone or folded into a broader terminal-family follow-on

## Promotion Rule
- promote when the proposal names one bounded integrated hard-sigmoid-enabled `nm1`
  path, keeps the first remote evaluation focused on physical source evidence,
  and explicitly defers Layer 2 hard-sigmoid evaluation until that source exists
