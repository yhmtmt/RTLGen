# NPU nm1 tanh vec enable

- item_id: `item_l1_npu_nm1_tanh_vec_enable_v1`
- layer: `layer1`
- kind: `circuit`
- status: `merged`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-24T12:15:00Z`
- updated_utc: `2026-03-24T12:58:59Z`
- proposal_id: `prop_l1_npu_nm1_tanh_vec_enable_v1`
- proposal_path: `docs/developer_loop/prop_l1_npu_nm1_tanh_vec_enable_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_activation_family_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l1_terminal_tanh_block_v1/analysis_report.md`
  - `docs/developer_loop/prop_l1_terminal_tanh_block_v1/promotion_decision.json`
  - `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/promotion_result.json`

## Problem
- the standalone terminal tanh wrapper now has accepted physical metrics, but
  later Layer 2 terminal `tanh` evaluation still requires an integrated
  tanh-enabled `nm1` source rather than a standalone activation wrapper
- current `npu_fp16_cpp_nm1_cmp` still exposes only vec ops `add/mul/relu`

## Candidate Idea
- integrate bounded int8 tanh support into the fixed `nm1` vec path
- generate a tanh-enabled `nm1` design/config variant
- run Layer 1 physical characterization for an integrated architecture-block
  proof target before any Layer 2 tanh campaigns are queued

## Why It Might Matter
- creates the correct physical source for later tanh Layer 2 perf campaigns
- prevents invalid Layer 2 evaluation grounded on sigmoid-only or relu-only NPU hardware
- keeps the lower-layer / higher-layer contract technically consistent

## Required Work
- l1 change: yes
- l2 change: not in this proposal
- mapper change: not in this proposal
- quality gate required: no separate model-quality gate at this stage; output quality belongs to later Layer 2 use of the block

## Evaluation Sketch
- local:
  - integrate bounded `int8` tanh into the `nm1` vec path
  - add legality / smoke checks
- remote:
  - first-stage integrated Layer 1 `architecture_block` physical sweep
  - accept one reduced physical source before reopening Layer 2 `tanh`
- follow-on:
  - use the accepted integrated source to seed bounded Layer 2 terminal `tanh`
    direct-output evaluation

## Inputs / Sources
- `docs/developer_loop/prop_l1_terminal_tanh_block_v1/analysis_report.md`
- `docs/developer_loop/prop_l1_terminal_tanh_block_v1/promotion_result.json`
- `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/analysis_report.md`
- discussion on 2026-03-24 about stepping from standalone tanh grounding to an integrated `nm1` source before any Layer 2 tanh campaign

## Open Questions
- whether the same reduced-proxy pattern used for sigmoid is sufficient for tanh
- what hierarchy policy is needed to keep integrated tanh `nm1` synthesis practical
- whether an integrated legality checkpoint should be accepted before the first reduced physical source

## Promotion Rule
- promote when the proposal names one bounded integrated tanh-enabled `nm1`
  path, keeps the first remote evaluation focused on physical source evidence,
  and explicitly defers Layer 2 tanh evaluation until that source exists

## Outcome
- accepted physical evidence: PR `#81` / item `l1_prop_l1_npu_nm1_tanh_vec_enable_v1_r2`
- accepted best reduced-proxy point:
  - `param_hash`: `bf5fc187`
  - `critical_path_ns`: `2.8082`
  - `die_area`: `1440000.0`
  - `total_power_mw`: `0.000358`
- follow-on: seed bounded Layer 2 tanh direct-output work
