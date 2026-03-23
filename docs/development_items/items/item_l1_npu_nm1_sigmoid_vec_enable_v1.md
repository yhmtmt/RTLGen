# NPU nm1 sigmoid vec enable

- item_id: `item_l1_npu_nm1_sigmoid_vec_enable_v1`
- layer: `layer1`
- kind: `circuit`
- status: `merged`
- priority: `high`
- owner: `developer_agent`
- created_utc: `2026-03-19T13:10:00Z`
- updated_utc: `2026-03-23T22:47:46Z`
- proposal_id: `prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- proposal_path: `docs/developer_loop/prop_l1_npu_nm1_sigmoid_vec_enable_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_activation_family_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l1_terminal_sigmoid_block_v1/analysis_report.md`
  - `docs/developer_loop/prop_l1_terminal_sigmoid_block_v1/promotion_decision.json`
  - `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1/proposal.json`

## Problem
- the standalone terminal sigmoid wrapper has accepted physical metrics, but
  Layer 2 activation-family evaluation still required an integrated sigmoid-enabled
  `nm1` source rather than a standalone activation wrapper
- current `npu_fp16_cpp_nm1_cmp` exposed only vec ops `add/mul/relu`

## Candidate Idea
- integrate bounded int8 sigmoid support into the fixed `nm1` vec path
- generate a sigmoid-enabled `nm1` design/config variant
- run Layer 1 physical characterization for an integrated architecture-block
  proof target before any Layer 2 sigmoid campaigns are queued

## Why It Mattered
- created the correct physical source for later sigmoid Layer 2 perf campaigns
- prevented invalid Layer 2 evaluation grounded on `relu`-only NPU hardware
- kept the lower-layer / higher-layer contract technically consistent

## Outcome
- accepted legality checkpoint: PR `#69` / item `r14`
- accepted physical evidence: PR `#74` / item `r18`
- accepted best reduced-proxy point:
  - `param_hash`: `b5526579`
  - `critical_path_ns`: `2.7883`
  - `die_area`: `1440000.0`
  - `total_power_mw`: `0.00036`
- follow-on: unblock `prop_l2_mapper_terminal_activation_family_v1`
