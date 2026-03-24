# Terminal activation-family direct output

- item_id: `item_l2_mapper_terminal_activation_family_v1`
- layer: `layer2`
- kind: `mapper`
- status: `merged`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-19T11:20:00Z`
- updated_utc: `2026-03-24T09:17:16Z`
- proposal_id: `prop_l2_mapper_terminal_activation_family_v1`
- proposal_path: `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- triggering_evidence:
  - `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/analysis_report.md`
  - `docs/developer_loop/prop_l2_mapper_terminal_vecop_direct_output_v1/promotion_decision.json`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_measurement_r2/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_vecop_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_vecop_direct_output_v1_nm1_fused_r1/report.md`

## Problem
- direct terminal-output lowering is now proven for:
  - final GEMM writeback
  - final GEMM + `Relu`
  - standalone terminal `Relu` vec-op tails
- the next remaining gap was broader terminal activation support, especially
  non-linear activation families that are likely to require explicit quality
  gates and clearer legality handling than `Relu`
- broad architecture ranking was still the wrong next question; the limiting
  factor remained mapper and lowering coverage

## Candidate Idea
- define a bounded terminal activation family beyond standalone `Relu`, starting
  from a tiny nonlinear set on fixed `nm1`
- in the first blocked follow-on, assume both:
  - an accepted standalone Layer 1 `int8` sigmoid block
  - an accepted integrated sigmoid-enabled `nm1` NPU block
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
- l1 change: yes for the first pass
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
- which bounded nonlinear family is the best next step after the accepted
  sigmoid-first proof: keep extending `Sigmoid`, add `Tanh`, or choose another
  tiny activation set
- what stronger local output-quality threshold is required before broadening
  beyond this first bounded sigmoid scope
- whether the current schedule IR needs any additional terminal vec-op metadata
  beyond the accepted sigmoid path

## Promotion Rule
- promote when the proposal names a bounded nonlinear activation family,
  requires a quality gate, and keeps the remote evaluation staged as
  `measurement_only` first and dependency-gated `paired_comparison` second

## Promotion Outcome
- promoted to `docs/developer_loop/prop_l2_mapper_terminal_activation_family_v1`
- promotion rationale:
  - the bounded sigmoid-first activation family was specific enough to support
    a clean measurement-first proof
  - the next limiting factor was mapper lowering and staged evaluation order,
    not another broad ranking sweep

## Completion Outcome
- merged lower-layer prerequisites:
  - standalone sigmoid block PR `#63`
  - integrated sigmoid-enabled `nm1` source PR `#74`
- merged evidence:
  - measurement baseline PR `#75`
  - paired comparison PR `#76`
- result:
  - bounded terminal sigmoid direct-output lowering improved latency and energy
    across the whole sigmoid-first suite on fixed `nm1`
- workflow note:
  - the accepted evidence remains grounded by the reduced
    `npu_fp16_cpp_nm1_sigmoidproxy` architecture-block source rather than full
    `npu_top`
- next direction:
  - expand mapper or lowering support to the next bounded nonlinear activation
    family using the same dependency-ordered staged evaluation model
