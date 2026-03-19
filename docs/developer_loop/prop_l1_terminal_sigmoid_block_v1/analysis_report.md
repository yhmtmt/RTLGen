# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_terminal_sigmoid_block_v1`
- `candidate_id`: `l1_prop_l1_terminal_sigmoid_block_v1_nangate45_r3`

## Evaluations Consumed
- PR `#63` merged at `2026-03-19T13:00:39Z`
- Layer 1 DB item `l1_prop_l1_terminal_sigmoid_block_v1_nangate45_r3`
- accepted evidence:
  - `control_plane/shadow_exports/l1_promotions/l1_prop_l1_terminal_sigmoid_block_v1_nangate45_r3.json`
  - `runs/designs/activations/terminal_sigmoid_int8_pwl_wrapper/metrics.csv`
  - `runs/index.csv`

## Baseline Comparison
- no prior accepted Layer 1 terminal sigmoid block existed in the repo
- this proposal established the first accepted physical point set for a bounded
  `int8` sigmoid `pwl` wrapper on Nangate45
- accepted best point from the merged evidence:
  - `param_hash`: `d3ba16d6`
  - `critical_path_ns`: `0.1904`
  - `die_area`: `25600.0`
  - `total_power_mw`: `5.84e-05`
  - `metrics_csv`: `runs/designs/activations/terminal_sigmoid_int8_pwl_wrapper/metrics.csv`

## Result
- result: accepted first-pass physical seed for bounded `int8` sigmoid
- confidence level: medium
- estimated optimization room: moderate
- circuit conclusion robustness: sufficient for downstream Layer 2
  measurement-first use on fixed `nm1`

## Failures and Caveats
- the initial DB-native sweep failed first on config snapshot path hygiene and
  then on tiny-block PDN floorplan assumptions; both were corrected before the
  accepted rerun
- this proposal does not establish numerical quality beyond local smoke checks;
  output-quality comparison remains a later Layer 2 responsibility
- the accepted implementation is intentionally `int8` `pwl`, not native `fp16`

## Recommendation
- promote this Layer 1 block as the prerequisite physical source for
  `prop_l2_mapper_terminal_activation_family_v1`
- keep follow-on nonlinear activation-family work bounded to fixed `nm1` and
  measurement-first evaluation modes
