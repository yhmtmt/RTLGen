# Terminal vec-op direct output

- item_id: `item_l2_mapper_terminal_vecop_direct_output_v1`
- layer: `layer2`
- kind: `mapper`
- status: `merged`
- priority: `medium`
- owner: `developer_agent`
- created_utc: `2026-03-18T14:05:00Z`
- updated_utc: `2026-03-19T11:14:02Z`
- proposal_id: `prop_l2_mapper_terminal_vecop_direct_output_v1`
- proposal_path: `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1`
- triggered_by_proposal: `prop_l2_mapper_terminal_op_generalization_v1`
- triggering_evidence:
  - `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/analysis_report.md`
  - `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/promotion_decision.json`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_submit_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_measurement_r1/report.md`
  - `runs/campaigns/npu/e2e_eval_onnx_terminal_direct_output_suite_fused_nm1_v1__l2_prop_l2_mapper_terminal_op_generalization_v1_nm1_fused_r1/report.md`

## Problem
- direct terminal-output lowering is now proven for final GEMM outputs and
  final GEMM+`Relu` epilogues on fixed `nm1`
- broader terminal-op claims are still blocked because the current mapper does
  not expose a direct-output path for terminal standalone vector-like tails
- that means the next bottleneck is mapper or lowering support for terminal
  vec-op families rather than another ranking sweep on the already-accepted
  GEMM-tail path

## Candidate Idea
- add a bounded direct-output path for terminal vec-op style tails, starting
  from the smallest family that is legal to express in the current schedule IR
- stage the work measurement-first so refreshed non-fused references are
  recorded before any paired direct-output comparison is judged

## Why It Might Matter
- extends the accepted direct-output mechanism beyond final GEMM writeback
- tests whether the remaining tail DMA cost can also be removed when the final
  op is not just a GEMM destination
- creates a cleaner bridge toward broader activation or elementwise terminal-op
  support without reopening architecture ranking too early

## Required Work
- l1 change: no for the first pass
- l2 change: no new hardware in the first pass
- mapper change: yes
- quality gate required: likely yes if the chosen vec-op family affects output
  semantics or numerical tolerance

## Evaluation Sketch
- local:
  - define the smallest terminal vec-op family that can be expressed and
    checked cleanly
  - add mapper tests for non-fused vs direct-output schedule emission
  - add a quality gate if the chosen terminal op is numerically sensitive
- remote:
  - first-stage: `measurement_only` on fixed `nm1` non-fused references for the
    bounded terminal vec-op suite
  - second-stage: `paired_comparison` on the same points after terminal vec-op
    direct-output lowering is enabled
  - defer broad ranking until the vec-op comparison result is accepted

## Inputs / Sources
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/analysis_report.md`
- `docs/proposals/prop_l2_mapper_terminal_op_generalization_v1/promotion_decision.json`
- merged evidence from PRs `#54` and `#56`
- discussion on 2026-03-18 about moving next to broader terminal-op family
  support instead of reopening ranking

## Open Questions
- which terminal vec-op family is the smallest useful next step:
  standalone `Relu`, a tiny activation set, or a more generic vec-op path
- whether the current schedule IR and perf path already have enough structure
  for a clean direct-output proof without adding new descriptor semantics
- what measurement-only reference suite is representative enough without
  becoming another broad model-support claim

## Promotion Rule
- promote when the proposal names a bounded terminal vec-op family, keeps the
  first remote stage as `measurement_only`, and treats broad ranking as
  follow-on work rather than first-stage proof

## Promotion Outcome
- promoted to `docs/proposals/prop_l2_mapper_terminal_vecop_direct_output_v1`
- promotion rationale:
  - the bounded standalone terminal `Relu` vec-op family was specific enough to
    support a clean measurement-first proof
  - the next limiting factor was mapper lowering and staged evaluation order,
    not another broad ranking sweep

## Completion Outcome
- merged evidence:
  - measurement baseline PR `#58`
  - paired comparison PR `#61`
- result:
  - bounded terminal vec-op direct-output lowering improved latency and energy
    across the whole standalone terminal `Relu` suite on fixed `nm1`
- workflow note:
  - the first paired PR `#60` was superseded after exposing a real dependency
    ordering gap between merged baseline evidence and paired candidate export
- next direction:
  - expand mapper or lowering support to broader terminal vec-op or activation
    families using the new dependency-ordered evaluation model
