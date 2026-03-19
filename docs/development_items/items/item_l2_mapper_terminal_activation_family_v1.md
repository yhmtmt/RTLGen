# Terminal activation-family direct output

- item_id: `item_l2_mapper_terminal_activation_family_v1`
- layer: `layer2`
- kind: `mapper`
- status: `promoted_to_proposal`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-19T11:20:00Z`
- updated_utc: `2026-03-19T11:20:00Z`
- proposal_id: `prop_l2_mapper_terminal_activation_family_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/analysis_report.md`
  - `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/promotion_decision.json`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1/report.md`

## Problem
- direct terminal-output lowering is now accepted for:
  - final GEMM writeback
  - final GEMM + `Relu`
  - standalone terminal `Relu` vec-op tails
- the next remaining gap is broader terminal activation support, especially
  non-linear activation families that are likely to require explicit quality
  gates and clearer legality handling than `Relu`
- broad architecture ranking is still the wrong next question; the limiting
  factor remains mapper and lowering coverage

## Candidate Idea
- define a bounded terminal activation family beyond standalone `Relu`, starting
  from a tiny nonlinear set on fixed `nm1`
- keep the same staged workflow:
  - `measurement_only` non-fused references first
  - `paired_comparison` only after baseline evidence is merged and materialized

## Why It Might Matter
- tests whether the accepted direct-output mechanism extends to a more
  numerically sensitive terminal-op family
- forces the quality-gate path and dependency-ordered evaluation flow to stay
  explicit
- creates a cleaner bridge toward broader activation support without reopening
  `nm1`/`nm2` ranking too early

## Required Work
- l1 change: no for the first pass
- l2 change: no new hardware for the first pass
- mapper change: yes
- quality gate required: yes

## Evaluation Sketch
- local:
  - choose the smallest useful nonlinear activation family beyond `Relu`
  - add legality tests for non-fused and direct-output lowering
  - define a local quality gate before remote spend
- remote:
  - first-stage: `measurement_only` on fixed `nm1` non-fused references
  - second-stage: `paired_comparison` on the same points with explicit
    dependency ordering on the merged baseline item
  - broad ranking remains deferred

## Inputs / Sources
- `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/analysis_report.md`
- `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/promotion_decision.json`
- merged evidence from PRs `#58` and `#61`
- discussion on 2026-03-19 about enforcing dependency ordering before paired
  export and about using measurement-only items for pure metric collection

## Open Questions
- which bounded nonlinear family is the best next step:
  terminal `Sigmoid` only, `Sigmoid + Tanh`, or another tiny activation set
- what local output-quality threshold is required before remote evaluation
- whether the current schedule IR needs any additional terminal vec-op metadata
  beyond the accepted standalone `Relu` path

## Promotion Rule
- promote when the proposal names a bounded nonlinear activation family,
  requires a quality gate, and keeps the remote evaluation staged as
  `measurement_only` first and dependency-gated `paired_comparison` second
