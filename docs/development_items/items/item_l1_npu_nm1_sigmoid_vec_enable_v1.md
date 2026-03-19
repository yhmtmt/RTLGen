# NPU nm1 sigmoid vec enable

- item_id: `item_l1_npu_nm1_sigmoid_vec_enable_v1`
- layer: `layer1`
- kind: `circuit`
- status: `promoted_to_proposal`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-19T13:10:00Z`
- updated_utc: `2026-03-19T13:10:00Z`
- proposal_id: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- proposal_path: `docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_activation_family_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l1_terminal_sigmoid_block_v1/analysis_report.md`
  - `docs/developer_loop/prop_l1_terminal_sigmoid_block_v1/promotion_decision.json`
  - `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/proposal.json`

## Problem
- the standalone terminal sigmoid wrapper now has accepted physical metrics
- Layer 2 activation-family evaluation still cannot use it directly, because
  campaign physical provenance comes from the hardened `nm1` NPU block, not the
  standalone activation wrapper
- current `npu_fp16_cpp_nm1_cmp` only enables vec ops `add/mul/relu`

## Candidate Idea
- integrate bounded int8 sigmoid support into the fixed `nm1` vec path
- generate a sigmoid-enabled `nm1` design/config variant
- run Layer 1 physical characterization for that integrated NPU block before
  any Layer 2 sigmoid campaigns are queued

## Why It Might Matter
- creates the correct physical source for later sigmoid Layer 2 perf campaigns
- prevents invalid Layer 2 evaluation grounded on `relu`-only NPU hardware
- keeps the two-layer contract technically consistent

## Required Work
- l1 change: yes
- l2 change: no in this proposal
- mapper change: no in this proposal
- quality gate required: local contract/legality only; model-quality remains a
  later Layer 2 concern

## Evaluation Sketch
- local:
  - add bounded sigmoid support to the NPU vec op path and descriptor contract
  - generate a sigmoid-enabled `nm1` block config/design
  - run local smoke and contract checks
- remote:
  - Layer 1 physical sweep for the sigmoid-enabled `nm1` block
- follow-on:
  - unblock `prop_l2_mapper_terminal_activation_family_v1`

## Promotion Rule
- promote when the proposal names one bounded sigmoid-enabled `nm1` design
  point, keeps the remote evaluation on integrated physical evidence, and
  clearly unblocks the Layer 2 activation-family measurement item
