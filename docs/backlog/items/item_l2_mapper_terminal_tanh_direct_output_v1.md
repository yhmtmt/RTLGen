# Terminal tanh direct output

- item_id: `item_l2_mapper_terminal_tanh_direct_output_v1`
- layer: `layer2`
- kind: `mapper`
- status: `promoted_to_proposal`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-24T13:10:00Z`
- updated_utc: `2026-03-24T13:10:00Z`
- proposal_id: `prop_l2_mapper_terminal_tanh_direct_output_v1`
- proposal_path: `docs/proposals/prop_l2_mapper_terminal_tanh_direct_output_v1`
- triggered_by_proposal: `prop_l1_npu_nm1_tanh_vec_enable_v1`
- triggering_evidence:
  - `docs/proposals/prop_l1_terminal_tanh_block_v1/analysis_report.md`
  - `docs/proposals/prop_l1_npu_nm1_tanh_vec_enable_v1/analysis_report.md`
  - `docs/proposals/prop_l1_npu_nm1_tanh_vec_enable_v1/promotion_decision.json`

## Problem
- the repo now has accepted lower-layer grounding for bounded terminal `tanh`:
  - standalone `int8` tanh block
  - integrated `nm1_tanhproxy` architecture-block source
- but there is no Layer 2 evidence yet showing whether terminal `tanh` can use the same direct vec-op output path that already won for sigmoid

## Candidate Idea
- run the same staged direct-output pattern for terminal `tanh` on fixed `nm1`:
  - `measurement_only` baseline first
  - dependency-gated `paired_comparison` second
- keep the scope bounded to a tiny tanh-first suite

## Why It Might Matter
- tests whether the accepted direct-output path extends cleanly from sigmoid to the next bounded nonlinear vec-op
- keeps the evaluation chain aligned with the abstraction-layer model:
  - lower-layer physical grounding first
  - workload-level comparison second

## Required Work
- l1 change: no
- l2 change: no new hardware for the first pass
- mapper change: yes
- quality gate required: yes

## Evaluation Sketch
- local:
  - add terminal `Tanh` mapper lowering
  - add legality tests for non-fused and direct-output lowering
  - generate a bounded tanh-first ONNX suite
- remote:
  - first-stage: `measurement_only` non-fused references on fixed `nm1`
  - second-stage: `paired_comparison` against the merged baseline

## Promotion Rule
- promote when the proposal keeps the remote evaluation staged as `measurement_only` first and dependency-gated `paired_comparison` second against the accepted integrated tanh source
