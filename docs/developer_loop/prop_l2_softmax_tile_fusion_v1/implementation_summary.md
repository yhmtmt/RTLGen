# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `title`: `Softmax-tail fused tile path`
- `status`: planning-approved, implementation not started

## Scope
- Bounded implementation target:
  - add a Layer 2 architecture variant that treats the imported softmax-tail
    path as a first-class architecture point rather than only reusing the
    existing integrated SOFTMAX baseline
  - add the mapper legality/lowering changes required to express that variant
    deterministically
  - keep the change scoped to the imported softmax-tail workload family first
- In scope:
  - architecture config additions for a fused softmax-tail candidate
  - mapper legality and lowering support for that candidate
  - campaign wiring needed to evaluate the candidate against the current
    softmax-tail baselines
- Out of scope for the first implementation pass:
  - broad redesign of the generic NPU shell
  - non-softmax workload retuning
  - wide Layer 1 circuit search beyond the current selected SOFTMAX seed
  - changes to external/manual evaluation lane procedure

## Files Changed
- Expected primary touch points:
  - `npu/arch/examples/`
  - `npu/arch/to_rtlgen.py`
  - `npu/rtlgen/gen.py`
  - `npu/mapper/`
  - `npu/eval/`
  - `runs/campaigns/npu/`
  - `npu/docs/status.md`
- Expected supporting touch points:
  - proposal-local artifacts under
    `docs/developer_loop/prop_l2_softmax_tile_fusion_v1/`
- Current code-change state:
  - no implementation diff yet
  - this document defines the bounded implementation slice before editing code

## Local Validation
- Planning validation completed:
  - reviewed current softmax-tail campaign baselines
  - reviewed current Layer 2 workflow and status docs
  - confirmed that mapper work is required before this architecture is
    evaluable
- Required local validation after implementation:
  - architecture/schema validation for the new candidate config
  - mapper legality/lowering smoke checks on the imported softmax-tail model
  - campaign manifest validation before remote execution
  - any existing local regressions directly touched by the mapper change
- Pass/fail summary:
  - planning pass complete
  - implementation validation pending code changes

## Evaluation Request
- Requested remote tasks after implementation:
  - `l2_campaign` with `objective=balanced`
  - `l2_campaign` with `objective=latency`
- Cost class:
  - both are `high`
- Required comparison baselines:
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/`
  - `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- Required evidence:
  - campaign report
  - summary.csv
  - best_point.json
  - generated campaign file used for the run
- Evaluation should not be requested until:
  - the mapper change is locally smoke-validated
  - the new candidate is expressible through the current Layer 2 campaign flow

## Risks
- Mapper legality may expand beyond a narrow softmax-tail special case and
  pull the proposal toward a broader scheduler change than intended.
- The fused path may improve only the tiny softmax-tail classifier and not
  produce a defensible general architectural recommendation.
- Added area or descriptor complexity may erase any latency gain.
- The current best integrated SOFTMAX baseline may already capture most of the
  practical benefit, leaving little room for a new architecture point.
