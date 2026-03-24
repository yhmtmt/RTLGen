# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_terminal_tanh_block_v1`
- `candidate_id`: `l1_prop_l1_terminal_tanh_block_v1_nangate45_r1`

## Evaluations Consumed
- PR `#80` merged at `2026-03-24T12:01:06Z`
- Layer 1 DB item `l1_prop_l1_terminal_tanh_block_v1_nangate45_r1`
- accepted evidence:
  - `control_plane/shadow_exports/l1_promotions/l1_prop_l1_terminal_tanh_block_v1_nangate45_r1.json`
  - `runs/designs/activations/terminal_tanh_int8_pwl_wrapper/metrics.csv`
  - `runs/index.csv`

## Baseline Comparison
- no prior accepted Layer 1 terminal tanh block existed in the repo
- this proposal establishes the first accepted physical point set for a bounded
  `int8` tanh `pwl` wrapper on Nangate45
- accepted best point from the merged evidence:
  - `param_hash`: `23010967`
  - `critical_path_ns`: `0.1899`
  - `die_area`: `25600.0`
  - `total_power_mw`: `0.000111`
  - `metrics_csv`: `runs/designs/activations/terminal_tanh_int8_pwl_wrapper/metrics.csv`

## Result
- result: accepted first-pass physical seed for bounded `int8` tanh
- confidence level: medium
- estimated optimization room: moderate
- circuit conclusion robustness: sufficient for downstream integrated
  `architecture_block` follow-on work

## Failures and Caveats
- this proposal establishes physical implementation only for the standalone
  bounded `int8` tanh wrapper, not integrated `nm1` enablement
- this proposal does not establish numerical model quality beyond local smoke
  checks; output-quality comparison remains a later Layer 2 responsibility
- the accepted implementation is intentionally `int8` `pwl`, not native `fp16`

## Recommendation
- promote this Layer 1 block as the prerequisite physical source for an
  integrated `nm1` tanh-enable follow-on
- keep the next step at `architecture_block` scope before reopening Layer 2
  terminal `tanh` direct-output evaluation
