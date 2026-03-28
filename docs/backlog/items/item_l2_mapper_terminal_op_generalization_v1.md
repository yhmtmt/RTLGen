# Generalized terminal-op direct output

- item_id: `item_l2_mapper_terminal_op_generalization_v1`
- layer: `layer2`
- kind: `mapper`
- status: `merged`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-16T06:00:00Z`
- updated_utc: `2026-03-18T13:52:04Z`
- proposal_id: `prop_l2_mapper_terminal_op_generalization_v1`
- proposal_path: `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1`
- triggered_by_proposal: `prop_cross_non_mlp_terminal_suite_v1`
- triggering_evidence:
  - `docs/proposals/prop_cross_non_mlp_terminal_suite_v1/analysis_report.md`
  - `docs/proposals/prop_cross_non_mlp_terminal_suite_v1/promotion_decision.json`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_submit_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_measurement_r1/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_softmax_suite_fused_output_nm1_v1__l2_prop_cross_non_mlp_terminal_suite_v1_nm1_fused_r1/report.md`

## Problem
- the fused terminal-output win is now established across a bounded softmax-tail
  suite, but the current mapper path is still specialized to terminal `Softmax`
- that means broader terminal-op claims would currently conflate mechanism
  generalization with unsupported lowering paths
- the next bottleneck is therefore mapper-side: identify a minimal direct-output
  generalization beyond `Softmax` without reopening broad architecture ranking

## Candidate Idea
- generalize the direct terminal-output lowering rule from softmax-only to a
  first-pass family of terminal linear plus terminal `Relu` outputs under the
  existing `nm1` hardware
- stage the work as measurement-first so the first remote spend only records
  non-fused reference metrics on a minimal generalized terminal-op suite

## Why It Might Matter
- tests whether the accepted direct-output mechanism extends beyond the current
  `Cast/Gemm/Softmax` subset
- creates a cleaner bridge from the bounded softmax proof to broader model
  support without spending on ranking noise too early
- keeps the next work item focused on mapper legality and schedule formation,
  which is the remaining limiting factor

## Required Work
- l1 change: no
- l2 change: no new hardware for the first pass
- mapper change: yes
- quality gate required: likely yes if new terminal ops or fused paths can
  affect numerical equivalence

## Evaluation Sketch
- local:
  - define the minimal eligible terminal-op family and legality rules
  - add mapper tests for non-fused vs direct-output schedule emission
  - add quality checks if the new terminal op can affect output semantics
- remote:
  - first-stage: `measurement_only` on fixed `nm1` non-fused reference points
    for the minimal generalized terminal-op suite
  - second-stage: `paired_comparison` on the same points after direct-output
    lowering is enabled for the chosen terminal ops
  - defer any broad ranking until the generalized terminal-op comparison is in

## Inputs / Sources
- `docs/proposals/prop_cross_non_mlp_terminal_suite_v1/analysis_report.md`
- `docs/proposals/prop_cross_non_mlp_terminal_suite_v1/promotion_decision.json`
- merged evidence from PRs `#49` and `#52`
- discussion on 2026-03-18 about metric-only measurement items and expected
  non-win/lose outcomes

## Open Questions
- whether terminal linear plus terminal `Relu` is still too close to the
  accepted softmax-tail proof
- whether the direct-output generalization should first target final GEMM
  writeback, final VEC writeback, or both
- what quality gate is required before spending remote evaluation budget

## Promotion Rule
- promote when the proposal names a bounded terminal-op family, keeps the first
  remote stage measurement-only, and delays broader ranking until the mapper
  generalization itself is proven or ruled out

## Promotion Outcome
- promoted to `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1`
- promotion rationale:
  - the merged softmax-suite evidence shows the direct-output mechanism is real
    across the bounded supported family
  - the next limiting factor is mapper generalization, not another broader
    ranking sweep on the same softmax-only lowering path

## Completion Outcome
- merged evidence:
  - measurement baseline PR `#54`
  - paired comparison PR `#56`
- result:
  - bounded direct terminal-output lowering for terminal linear plus terminal
    `Relu` improved latency and energy across the whole first-pass `nm1` suite
- next direction:
  - expand mapper or lowering support to broader terminal-op families before
    reopening broader architecture ranking
